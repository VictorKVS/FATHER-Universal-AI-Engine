from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.sourcecraft_adapter import SourceCraftAdapter
from providers.base import ProviderError


class SourceCraftAdapterTests(unittest.TestCase):
    def test_repository_must_be_org_repo(self) -> None:
        self.assertEqual(
            SourceCraftAdapter.split_repository("org/repo"),
            ("org", "repo"),
        )
        with self.assertRaises(ValueError):
            SourceCraftAdapter.split_repository("repo")

    def test_live_state_is_normalized(self) -> None:
        adapter = SourceCraftAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/repos/org/repo":
                return {
                    "slug": "repo",
                    "default_branch": "main",
                    "visibility": "private",
                    "organization": {"slug": "org"},
                    "web_url": "https://sourcecraft.dev/org/repo",
                }
            if path.endswith("/branches"):
                return {
                    "branches": [
                        {
                            "name": "feature/demo",
                            "commit": {"hash": "abc123"},
                        }
                    ]
                }
            if path.endswith("/pulls"):
                return {
                    "pull_requests": [
                        {
                            "slug": "pr-7",
                            "title": "Demo PR",
                            "status": "draft",
                            "source_branch": "feature/demo",
                            "target_branch": "main",
                            "source": {"ref": "feature/demo", "sha": "abc123"},
                            "target": {"ref": "main", "sha": "def456"},
                        }
                    ]
                }
            if path.endswith("/cicd/runs"):
                return {
                    "runs": [
                        {
                            "id": "run-1",
                            "slug": "CI",
                            "status": "success",
                            "branch": "feature/demo",
                            "commit_hash": "abc123",
                        }
                    ]
                }
            raise AssertionError(path)

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state("org/repo", "feature/demo")

        self.assertEqual(result["provider"], "sourcecraft")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertIsNone(result["compare"]["ahead_by"])
        self.assertEqual(result["change_requests"][0]["number"], "pr-7")
        self.assertEqual(result["workflow_runs"][0]["conclusion"], "success")

    def test_open_change_request_reconciles_draft(self) -> None:
        adapter = SourceCraftAdapter(token="token")
        captured = {}

        def fake_mutate(method, path, payload):
            captured["payload"] = payload
            return {"slug": "pr-7"}

        with (
            patch.object(adapter, "_mutate", side_effect=fake_mutate),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "slug": "pr-7",
                    "title": "Demo PR",
                    "status": "draft",
                    "source_branch": "feature/demo",
                    "target_branch": "main",
                    "source": {"ref": "feature/demo", "sha": "abc123"},
                    "target": {"ref": "main", "sha": "def456"},
                },
            ),
        ):
            result = adapter.open_change_request(
                "org/repo",
                "Demo PR",
                "feature/demo",
                "main",
                draft=True,
            )

        self.assertTrue(result["reconciled"])
        self.assertTrue(result["draft"])
        self.assertFalse(captured["payload"]["publish"])

    def test_missing_branch_fails_closed(self) -> None:
        adapter = SourceCraftAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/repos/org/repo":
                return {"default_branch": "main", "organization": {"slug": "org"}}
            if path.endswith("/branches"):
                return {"branches": []}
            return {}

        with patch.object(adapter, "_request", side_effect=fake_request):
            with self.assertRaises(ProviderError):
                adapter.live_state("org/repo", "feature/demo")


if __name__ == "__main__":
    unittest.main()
