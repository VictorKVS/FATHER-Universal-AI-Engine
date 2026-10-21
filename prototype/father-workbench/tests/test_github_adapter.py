from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.github_adapter import GitHubAdapter, ProviderError


class GitHubAdapterTests(unittest.TestCase):
    def test_repository_must_be_owner_name(self) -> None:
        self.assertEqual(
            GitHubAdapter.split_repository("VictorKVS/FATHER-Universal-AI-Engine"),
            ("VictorKVS", "FATHER-Universal-AI-Engine"),
        )
        with self.assertRaises(ValueError):
            GitHubAdapter.split_repository("invalid")

    def test_branch_name_validation_rejects_dangerous_refs(self) -> None:
        for value in (
            "../main",
            "feature//double",
            "feature/test.lock",
            "feature/test name",
            "feature/test@{x}",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    GitHubAdapter.validate_branch_name(value)

    def test_create_branch_requires_write_credential(self) -> None:
        adapter = GitHubAdapter(token="")
        with self.assertRaises(ProviderError):
            adapter.create_branch("owner/repo", "feature/new", "main")

    def test_create_branch_reconciles_provider_state(self) -> None:
        adapter = GitHubAdapter(token="token")

        def fake_request(path: str, query=None):
            if "/git/ref/heads/" in path:
                return {"object": {"sha": "base123"}}
            if "/branches/" in path:
                return {"commit": {"sha": "base123"}}
            raise AssertionError(path)

        with (
            patch.object(adapter, "_request", side_effect=fake_request),
            patch.object(
                adapter,
                "_mutate",
                return_value={
                    "ref": "refs/heads/feature/new",
                    "object": {"sha": "base123"},
                },
            ),
        ):
            result = adapter.create_branch(
                "owner/repo",
                "feature/new",
                "main",
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["head_sha"], "base123")

    def test_live_state_is_normalized(self) -> None:
        adapter = GitHubAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path.endswith("/repos/VictorKVS/FATHER-Universal-AI-Engine"):
                return {
                    "full_name": "VictorKVS/FATHER-Universal-AI-Engine",
                    "private": False,
                    "default_branch": "main",
                    "archived": False,
                    "visibility": "public",
                }
            if "/branches/" in path:
                return {"commit": {"sha": "abc123"}, "protected": False}
            if "/compare/" in path:
                return {
                    "status": "ahead",
                    "ahead_by": 2,
                    "behind_by": 0,
                    "total_commits": 2,
                }
            if path.endswith("/pulls"):
                return [
                    {
                        "number": 7,
                        "title": "Prototype",
                        "state": "open",
                        "draft": True,
                        "html_url": "https://example.invalid/pr/7",
                        "head": {"sha": "abc123"},
                        "base": {"ref": "main"},
                        "user": {"login": "tester", "type": "User"},
                        "updated_at": "2026-10-21T00:00:00Z",
                    }
                ]
            if path.endswith("/check-runs"):
                return {
                    "check_runs": [
                        {
                            "id": 1,
                            "name": "tests",
                            "status": "completed",
                            "conclusion": "success",
                        }
                    ]
                }
            if path.endswith("/status"):
                return {"state": "success", "total_count": 0, "statuses": []}
            if path.endswith("/actions/runs"):
                return {
                    "workflow_runs": [
                        {
                            "id": 9,
                            "name": "CI",
                            "event": "push",
                            "status": "completed",
                            "conclusion": "success",
                            "head_sha": "abc123",
                        }
                    ]
                }
            raise AssertionError(path)

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state(
                "VictorKVS/FATHER-Universal-AI-Engine",
                "feature/example",
            )

        self.assertEqual(result["provider"], "github")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["compare"]["ahead_by"], 2)
        self.assertEqual(result["change_requests"][0]["number"], 7)
        self.assertEqual(result["checks"][0]["conclusion"], "success")
        self.assertEqual(result["workflow_runs"][0]["conclusion"], "success")

    def test_missing_head_sha_fails_closed(self) -> None:
        adapter = GitHubAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if "/branches/" in path:
                return {"commit": {}}
            return {"default_branch": "main"}

        with patch.object(adapter, "_request", side_effect=fake_request):
            with self.assertRaises(ProviderError):
                adapter.live_state("owner/repo", "feature/test")


if __name__ == "__main__":
    unittest.main()
