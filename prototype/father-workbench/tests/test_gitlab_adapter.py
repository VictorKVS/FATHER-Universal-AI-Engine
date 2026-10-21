from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.gitlab_adapter import GitLabAdapter
from providers.github_adapter import ProviderError


class GitLabAdapterTests(unittest.TestCase):
    def test_project_path_requires_namespace(self) -> None:
        self.assertEqual(
            GitLabAdapter.project_path("group/project"),
            "group/project",
        )
        with self.assertRaises(ValueError):
            GitLabAdapter.project_path("project")

    def test_create_branch_requires_write_credential(self) -> None:
        adapter = GitLabAdapter(token="")
        with self.assertRaises(ProviderError):
            adapter.create_branch("group/project", "feature/new", "main")

    def test_create_branch_reconciles_provider_state(self) -> None:
        adapter = GitLabAdapter(token="token")

        with (
            patch.object(
                adapter,
                "_mutate",
                return_value={
                    "name": "feature/new",
                    "commit": {"id": "base123"},
                },
            ),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "name": "feature/new",
                    "commit": {"id": "base123"},
                    "web_url": "https://gitlab.example/group/project/-/tree/feature/new",
                },
            ),
        ):
            result = adapter.create_branch(
                "group/project",
                "feature/new",
                "main",
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["head_sha"], "base123")

    def test_open_change_request_reconciles_provider_state(self) -> None:
        adapter = GitLabAdapter(token="token")
        captured = {}

        def fake_mutate(method, path, payload):
            captured["payload"] = payload
            return {"iid": 12}

        with (
            patch.object(adapter, "_mutate", side_effect=fake_mutate),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "iid": 12,
                    "title": "Draft: Demo MR",
                    "state": "opened",
                    "draft": True,
                    "source_branch": "feature/demo",
                    "target_branch": "main",
                    "sha": "abc123",
                    "web_url": "https://gitlab.example/mr/12",
                },
            ),
        ):
            result = adapter.open_change_request(
                "group/project",
                "Demo MR",
                "feature/demo",
                "main",
                draft=True,
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["number"], 12)
        self.assertEqual(captured["payload"]["title"], "Draft: Demo MR")
        self.assertEqual(result["head_ref"], "feature/demo")

    def test_live_state_is_normalized(self) -> None:
        adapter = GitLabAdapter(
            token="not-used",
            base_url="https://gitlab.example",
        )

        def fake_request(path: str, query=None):
            if path == "/projects/group%2Fproject":
                return {
                    "path_with_namespace": "group/project",
                    "default_branch": "main",
                    "visibility": "private",
                    "archived": False,
                    "web_url": "https://gitlab.example/group/project",
                }
            if "/repository/branches/" in path:
                return {
                    "name": "feature/demo",
                    "protected": False,
                    "commit": {"id": "abc123"},
                }
            if path.endswith("/repository/compare"):
                return {
                    "commits": [{"id": "abc123"}, {"id": "def456"}],
                    "diffs": [{"old_path": "a", "new_path": "b"}],
                }
            if path.endswith("/merge_requests"):
                return [
                    {
                        "iid": 3,
                        "title": "Demo MR",
                        "state": "opened",
                        "draft": True,
                        "web_url": "https://gitlab.example/mr/3",
                        "sha": "abc123",
                        "source_branch": "feature/demo",
                        "target_branch": "main",
                        "updated_at": "2026-10-21T00:00:00Z",
                    }
                ]
            if path.endswith("/pipelines"):
                return [
                    {
                        "id": 99,
                        "source": "push",
                        "status": "success",
                        "sha": "abc123",
                        "web_url": "https://gitlab.example/pipelines/99",
                    }
                ]
            raise AssertionError(path)

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state(
                "group/project",
                "feature/demo",
            )

        self.assertEqual(result["provider"], "gitlab")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["compare"]["ahead_by"], 2)
        self.assertEqual(result["change_requests"][0]["number"], 3)
        self.assertEqual(result["workflow_runs"][0]["status"], "success")

    def test_missing_head_sha_fails_closed(self) -> None:
        adapter = GitLabAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/projects/group%2Fproject":
                return {"default_branch": "main"}
            if "/repository/branches/" in path:
                return {"commit": {}}
            return {}

        with patch.object(adapter, "_request", side_effect=fake_request):
            with self.assertRaises(ProviderError):
                adapter.live_state("group/project", "feature/demo")


if __name__ == "__main__":
    unittest.main()
