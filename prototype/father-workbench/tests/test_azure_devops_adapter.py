from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.azure_devops_adapter import AzureDevOpsAdapter
from providers.base import ProviderError


class AzureDevOpsAdapterTests(unittest.TestCase):
    def test_repository_binding_has_three_parts(self) -> None:
        self.assertEqual(
            AzureDevOpsAdapter.split_repository("org/project/repo"),
            ("org", "project", "repo"),
        )
        with self.assertRaises(ValueError):
            AzureDevOpsAdapter.split_repository("project/repo")

    def test_live_state_is_normalized(self) -> None:
        adapter = AzureDevOpsAdapter(token="token")

        def fake_request(path: str, query=None):
            if path.endswith("/_apis/git/repositories/repo"):
                return {
                    "name": "repo",
                    "defaultBranch": "refs/heads/main",
                    "webUrl": "https://dev.azure.com/org/project/_git/repo",
                }
            if path.endswith("/refs"):
                return {
                    "value": [{
                        "name": "refs/heads/feature/demo",
                        "objectId": "abc123",
                        "statuses": [{
                            "id": 1,
                            "state": "succeeded",
                            "context": {"name": "CI"},
                        }],
                    }]
                }
            if path.endswith("/pullrequests"):
                return {
                    "value": [{
                        "pullRequestId": 7,
                        "title": "Demo PR",
                        "status": "active",
                        "isDraft": True,
                        "sourceRefName": "refs/heads/feature/demo",
                        "targetRefName": "refs/heads/main",
                        "lastMergeSourceCommit": {"commitId": "abc123"},
                    }]
                }
            raise AssertionError((path, query))

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state(
                "org/project/repo",
                "feature/demo",
            )

        self.assertEqual(result["provider"], "azure_devops")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["change_requests"][0]["number"], 7)
        self.assertEqual(result["checks"][0]["name"], "CI")

    def test_create_branch_reconciles(self) -> None:
        adapter = AzureDevOpsAdapter(token="token")
        refs = [
            {"name": "refs/heads/main", "objectId": "base123"},
            {"name": "refs/heads/feature/new", "objectId": "base123"},
        ]

        def fake_ref(root, branch, include_statuses=False):
            return refs[0] if branch == "main" else refs[1]

        with (
            patch.object(adapter, "_ref", side_effect=fake_ref),
            patch.object(
                adapter,
                "_mutate",
                return_value={
                    "value": [{
                        "success": True,
                        "newObjectId": "base123",
                    }]
                },
            ),
        ):
            result = adapter.create_branch(
                "org/project/repo",
                "feature/new",
                "main",
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(result["head_sha"], "base123")

    def test_pull_request_reconciles(self) -> None:
        adapter = AzureDevOpsAdapter(token="token")

        with (
            patch.object(
                adapter,
                "_mutate",
                return_value={"pullRequestId": 12},
            ),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "pullRequestId": 12,
                    "title": "Demo PR",
                    "status": "active",
                    "isDraft": True,
                    "sourceRefName": "refs/heads/feature/demo",
                    "targetRefName": "refs/heads/main",
                    "lastMergeSourceCommit": {"commitId": "abc123"},
                },
            ),
        ):
            result = adapter.open_change_request(
                "org/project/repo",
                "Demo PR",
                "feature/demo",
                "main",
                draft=True,
            )

        self.assertTrue(result["reconciled"])
        self.assertTrue(result["draft"])
        self.assertEqual(result["number"], 12)

    def test_write_requires_credential(self) -> None:
        adapter = AzureDevOpsAdapter(token="")
        with self.assertRaises(ProviderError):
            adapter._mutate("POST", "/path", {})


if __name__ == "__main__":
    unittest.main()
