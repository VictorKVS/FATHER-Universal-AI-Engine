from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from providers.base import ProviderError
from providers.forgejo_adapter import ForgejoAdapter
from providers.gitea_adapter import GiteaAdapter


class GiteaCompatibleAdapterTests(unittest.TestCase):
    def _adapters(self):
        return (
            GiteaAdapter(token="token", base_url="https://gitea.example"),
            ForgejoAdapter(token="token", base_url="https://forgejo.example"),
        )

    def test_provider_ids_remain_distinct(self) -> None:
        gitea, forgejo = self._adapters()
        self.assertEqual(gitea.provider_id, "gitea")
        self.assertEqual(forgejo.provider_id, "forgejo")

    def test_live_state_is_normalized(self) -> None:
        for adapter in self._adapters():
            with self.subTest(provider=adapter.provider_id):
                def fake_request(path: str, query=None):
                    if path == "/repos/org/repo":
                        return {
                            "full_name": "org/repo",
                            "default_branch": "main",
                            "private": False,
                            "html_url": "https://example/org/repo",
                        }
                    if "/branches/" in path:
                        return {
                            "name": "feature/demo",
                            "protected": False,
                            "commit": {"id": "abc123"},
                        }
                    if "/compare/" in path:
                        return {
                            "commits": [{"sha": "abc123"}],
                            "total_commits": 1,
                        }
                    if path.endswith("/pulls"):
                        return [{
                            "number": 4,
                            "title": "Demo PR",
                            "state": "open",
                            "head": {"ref": "feature/demo", "sha": "abc123"},
                            "base": {"ref": "main"},
                        }]
                    if path.endswith("/actions/runs"):
                        return {
                            "workflow_runs": [{
                                "id": 8,
                                "name": "CI",
                                "status": "success",
                                "head_branch": "feature/demo",
                                "head_sha": "abc123",
                            }]
                        }
                    raise AssertionError((path, query))

                with patch.object(
                    adapter,
                    "_request",
                    side_effect=fake_request,
                ):
                    result = adapter.live_state(
                        "org/repo",
                        "feature/demo",
                    )

                self.assertEqual(result["provider"], adapter.provider_id)
                self.assertEqual(result["branch"]["head_sha"], "abc123")
                self.assertEqual(result["compare"]["ahead_by"], 1)
                self.assertEqual(result["change_requests"][0]["number"], 4)
                self.assertEqual(
                    result["workflow_runs"][0]["conclusion"],
                    "success",
                )

    def test_branch_creation_reconciles(self) -> None:
        for adapter in self._adapters():
            with self.subTest(provider=adapter.provider_id):
                captured = {}
                def fake_mutate(method, path, payload):
                    captured["payload"] = payload
                    return {
                        "name": "feature/new",
                        "commit": {"id": "base123"},
                    }

                with (
                    patch.object(
                        adapter,
                        "_mutate",
                        side_effect=fake_mutate,
                    ),
                    patch.object(
                        adapter,
                        "_request",
                        return_value={
                            "name": "feature/new",
                            "commit": {"id": "base123"},
                        },
                    ),
                ):
                    result = adapter.create_branch(
                        "org/repo",
                        "feature/new",
                        "main",
                    )

                self.assertTrue(result["reconciled"])
                self.assertEqual(
                    captured["payload"],
                    {
                        "new_branch_name": "feature/new",
                        "old_ref_name": "main",
                    },
                )

    def test_pull_request_reconciles(self) -> None:
        for adapter in self._adapters():
            with self.subTest(provider=adapter.provider_id):
                with (
                    patch.object(
                        adapter,
                        "_mutate",
                        return_value={"number": 5},
                    ),
                    patch.object(
                        adapter,
                        "_request",
                        return_value={
                            "number": 5,
                            "title": "Demo PR",
                            "state": "open",
                            "head": {
                                "ref": "feature/demo",
                                "sha": "abc123",
                            },
                            "base": {"ref": "main"},
                        },
                    ),
                ):
                    result = adapter.open_change_request(
                        "org/repo",
                        "Demo PR",
                        "feature/demo",
                        "main",
                        draft=False,
                    )

                self.assertTrue(result["reconciled"])
                self.assertEqual(result["number"], 5)
                self.assertFalse(result["draft"])

    def test_draft_fails_closed(self) -> None:
        for adapter in self._adapters():
            with self.subTest(provider=adapter.provider_id):
                with self.assertRaises(ValueError):
                    adapter.open_change_request(
                        "org/repo",
                        "Demo PR",
                        "feature/demo",
                        "main",
                        draft=True,
                    )

    def test_write_requires_credential(self) -> None:
        adapter = GiteaAdapter(
            token="",
            base_url="https://gitea.example",
        )
        with self.assertRaises(ProviderError):
            adapter.create_branch(
                "org/repo",
                "feature/new",
                "main",
            )


if __name__ == "__main__":
    unittest.main()
