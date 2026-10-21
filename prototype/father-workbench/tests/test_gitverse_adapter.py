from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.gitverse_adapter import GitVerseAdapter
from providers.base import ProviderError


class GitVerseAdapterTests(unittest.TestCase):
    def test_repository_must_be_owner_name(self) -> None:
        self.assertEqual(
            GitVerseAdapter.split_repository("org/repo"),
            ("org", "repo"),
        )
        with self.assertRaises(ValueError):
            GitVerseAdapter.split_repository("repo")

    def test_live_state_is_normalized(self) -> None:
        adapter = GitVerseAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/repos/org/repo":
                return {
                    "full_name": "org/repo",
                    "default_branch": "main",
                    "private": False,
                    "html_url": "https://gitverse.ru/org/repo",
                }
            if "/branches/" in path:
                return {
                    "name": "feature/demo",
                    "protected": False,
                    "commit": {"sha": "abc123"},
                }
            if "/compare/" in path:
                return {
                    "status": "ahead",
                    "ahead_by": 2,
                    "behind_by": 0,
                    "total_commits": 2,
                    "commits": [{"sha": "1"}, {"sha": "2"}],
                }
            if path.endswith("/pulls"):
                return [
                    {
                        "number": 7,
                        "title": "Demo PR",
                        "state": "open",
                        "draft": True,
                        "head": {"ref": "feature/demo", "sha": "abc123"},
                        "base": {"ref": "main"},
                        "html_url": "https://gitverse.ru/org/repo/pulls/7",
                    }
                ]
            if path.endswith("/actions/runs"):
                return {
                    "workflow_runs": [
                        {
                            "id": 99,
                            "title": "Build",
                            "status": "completed",
                            "conclusion": "success",
                            "commit_sha": "abc123",
                        }
                    ]
                }
            raise AssertionError(path)

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state("org/repo", "feature/demo")

        self.assertEqual(result["provider"], "gitverse")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["compare"]["ahead_by"], 2)
        self.assertEqual(result["change_requests"][0]["number"], 7)
        self.assertEqual(result["workflow_runs"][0]["conclusion"], "success")

    def test_missing_head_sha_fails_closed(self) -> None:
        adapter = GitVerseAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/repos/org/repo":
                return {"default_branch": "main"}
            if "/branches/" in path:
                return {"commit": {}}
            return {}

        with patch.object(adapter, "_request", side_effect=fake_request):
            with self.assertRaises(ProviderError):
                adapter.live_state("org/repo", "feature/demo")


if __name__ == "__main__":
    unittest.main()
