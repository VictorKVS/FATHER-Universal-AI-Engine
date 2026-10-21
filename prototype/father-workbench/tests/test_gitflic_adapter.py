from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.gitflic_adapter import GitFlicAdapter
from providers.base import ProviderError


class GitFlicAdapterTests(unittest.TestCase):
    def test_repository_must_be_owner_project(self) -> None:
        self.assertEqual(
            GitFlicAdapter.split_repository("owner/project"),
            ("owner", "project"),
        )
        with self.assertRaises(ValueError):
            GitFlicAdapter.split_repository("project")

    def test_live_state_is_normalized(self) -> None:
        adapter = GitFlicAdapter(token="not-used")

        def fake_request(path: str, query=None):
            if path == "/project/owner/project":
                return {
                    "id": "project-id",
                    "alias": "project",
                    "defaultBranch": "master",
                }
            if path.endswith("/branch") and query and "name" in query:
                return {
                    "name": "feature/demo",
                    "lastCommit": {"hash": "abc123"},
                }
            if path.endswith("/branch/compare"):
                return [{"newPath": "README.md"}]
            if path.endswith("/merge-request/list"):
                return {
                    "_embedded": {
                        "mergeRequestModelList": [
                            {
                                "localId": 3,
                                "title": "Demo MR",
                                "sourceBranch": {"id": "feature/demo", "hash": "abc123"},
                                "targetBranch": {"id": "master"},
                                "status": {"id": "OPENED"},
                            }
                        ]
                    }
                }
            if path.endswith("/cicd/pipeline"):
                return {
                    "_embedded": {
                        "restPipelineModelList": [
                            {
                                "id": "p1",
                                "status": "SUCCESS",
                                "commitHash": "abc123",
                            }
                        ]
                    }
                }
            raise AssertionError((path, query))

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state("owner/project", "feature/demo")

        self.assertEqual(result["provider"], "gitflic")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["compare"]["changed_files"], 1)
        self.assertEqual(result["change_requests"][0]["number"], 3)
        self.assertEqual(result["workflow_runs"][0]["conclusion"], "success")

    def test_create_branch_reconciles_provider_state(self) -> None:
        adapter = GitFlicAdapter(token="token")
        with (
            patch.object(
                adapter,
                "_mutate",
                return_value={
                    "name": "feature/new",
                    "lastCommit": {"hash": "abc123"},
                },
            ),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "name": "feature/new",
                    "lastCommit": {"hash": "abc123"},
                },
            ),
        ):
            result = adapter.create_branch(
                "owner/project",
                "feature/new",
                "master",
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["head_sha"], "abc123")

    def test_draft_merge_request_fails_closed(self) -> None:
        adapter = GitFlicAdapter(token="token")
        with self.assertRaises(ValueError):
            adapter.open_change_request(
                "owner/project",
                "Demo MR",
                "feature/demo",
                "master",
                draft=True,
            )

    def test_open_merge_request_reconciles_provider_state(self) -> None:
        adapter = GitFlicAdapter(token="token")

        def fake_request(path: str, query=None):
            if path == "/project/owner/project":
                return {"id": "project-id"}
            if path.endswith("/merge-request/8"):
                return {
                    "id": "mr-id",
                    "localId": 8,
                    "title": "Demo MR",
                    "sourceBranch": {"id": "feature/demo", "hash": "abc123"},
                    "targetBranch": {"id": "master"},
                    "status": {"id": "OPENED"},
                }
            raise AssertionError(path)

        with (
            patch.object(
                adapter,
                "_mutate",
                return_value={"localId": 8},
            ),
            patch.object(adapter, "_request", side_effect=fake_request),
        ):
            result = adapter.open_change_request(
                "owner/project",
                "Demo MR",
                "feature/demo",
                "master",
                draft=False,
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["number"], 8)
        self.assertFalse(result["draft"])


if __name__ == "__main__":
    unittest.main()
