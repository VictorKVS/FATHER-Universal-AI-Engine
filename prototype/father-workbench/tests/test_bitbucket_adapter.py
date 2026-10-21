from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.bitbucket_adapter import BitbucketAdapter
from providers.base import ProviderError


class BitbucketAdapterTests(unittest.TestCase):
    def test_repository_must_be_workspace_repo(self) -> None:
        self.assertEqual(
            BitbucketAdapter.split_repository("team/repo"),
            ("team", "repo"),
        )
        with self.assertRaises(ValueError):
            BitbucketAdapter.split_repository("repo")

    def test_live_state_is_normalized(self) -> None:
        adapter = BitbucketAdapter(token="token")

        def fake_request(path: str, query=None):
            if path == "/repositories/team/repo":
                return {
                    "full_name": "team/repo",
                    "is_private": True,
                    "mainbranch": {"name": "main"},
                    "links": {"html": {"href": "https://bitbucket.org/team/repo"}},
                }
            if path.endswith("/refs/branches/feature%2Fdemo"):
                return {
                    "name": "feature/demo",
                    "target": {"hash": "abc123"},
                }
            if path.endswith("/pullrequests"):
                return {
                    "values": [{
                        "id": 7,
                        "title": "Demo PR",
                        "state": "OPEN",
                        "draft": True,
                        "source": {
                            "branch": {"name": "feature/demo"},
                            "commit": {"hash": "abc123"},
                        },
                        "destination": {"branch": {"name": "main"}},
                    }]
                }
            if path.endswith("/pipelines"):
                return {
                    "values": [{
                        "uuid": "{run}",
                        "build_number": 9,
                        "state": {
                            "name": "COMPLETED",
                            "result": {"name": "SUCCESSFUL"},
                        },
                        "target": {
                            "ref_name": "feature/demo",
                            "commit": {"hash": "abc123"},
                        },
                    }]
                }
            raise AssertionError((path, query))

        with patch.object(adapter, "_request", side_effect=fake_request):
            result = adapter.live_state("team/repo", "feature/demo")

        self.assertEqual(result["provider"], "bitbucket")
        self.assertEqual(result["branch"]["head_sha"], "abc123")
        self.assertEqual(result["change_requests"][0]["number"], 7)
        self.assertEqual(result["workflow_runs"][0]["conclusion"], "success")

    def test_create_branch_reconciles(self) -> None:
        adapter = BitbucketAdapter(token="token")
        captured = {}

        def fake_request(path: str, query=None):
            if path.endswith("/refs/branches/main"):
                return {"name": "main", "target": {"hash": "base123"}}
            if path.endswith("/refs/branches/feature%2Fnew"):
                return {
                    "name": "feature/new",
                    "target": {"hash": "base123"},
                }
            raise AssertionError(path)

        def fake_mutate(method, path, payload):
            captured["payload"] = payload
            return {
                "name": "feature/new",
                "target": {"hash": "base123"},
            }

        with (
            patch.object(adapter, "_request", side_effect=fake_request),
            patch.object(adapter, "_mutate", side_effect=fake_mutate),
        ):
            result = adapter.create_branch(
                "team/repo",
                "feature/new",
                "main",
            )

        self.assertTrue(result["reconciled"])
        self.assertEqual(
            captured["payload"],
            {"name": "feature/new", "target": {"hash": "base123"}},
        )

    def test_pull_request_reconciles(self) -> None:
        adapter = BitbucketAdapter(token="token")
        captured = {}

        def fake_mutate(method, path, payload):
            captured["payload"] = payload
            return {"id": 11}

        with (
            patch.object(adapter, "_mutate", side_effect=fake_mutate),
            patch.object(
                adapter,
                "_request",
                return_value={
                    "id": 11,
                    "title": "Demo PR",
                    "state": "OPEN",
                    "draft": True,
                    "source": {
                        "branch": {"name": "feature/demo"},
                        "commit": {"hash": "abc123"},
                    },
                    "destination": {"branch": {"name": "main"}},
                },
            ),
        ):
            result = adapter.open_change_request(
                "team/repo",
                "Demo PR",
                "feature/demo",
                "main",
                draft=True,
            )

        self.assertTrue(result["reconciled"])
        self.assertTrue(captured["payload"]["draft"])
        self.assertEqual(result["number"], 11)

    def test_write_requires_credential(self) -> None:
        adapter = BitbucketAdapter(token="")
        with self.assertRaises(ProviderError):
            adapter.create_branch("team/repo", "feature/new", "main")


if __name__ == "__main__":
    unittest.main()
