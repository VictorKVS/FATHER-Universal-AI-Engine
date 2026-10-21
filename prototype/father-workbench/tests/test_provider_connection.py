from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import server
from provider_binding_store import ProviderBindingStore
from providers.base import ProviderError


class FakeEvidence:
    def __init__(self) -> None:
        self.evidence = []
        self.events = []

    def store_evidence(self, **kwargs):
        item = {
            "evidence_id": f"EVD-{len(self.evidence)+1}",
            "deduplicated": False,
            **kwargs,
        }
        self.evidence.append(item)
        return item

    def append_manufacturing_event(self, **kwargs):
        item = {
            "event_id": f"MFG-{len(self.events)+1}",
            **kwargs,
        }
        self.events.append(item)
        return item


class ProviderConnectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = {
            "project_id": "P-1",
            "repository": "owner/repo",
            "branch": "main",
            "dev_platform": {
                "primary_provider": "github",
                "repository": "owner/repo",
                "branch": "main",
            },
        }

    def _store_with_target(self, root: Path):
        store = ProviderBindingStore(root)
        _state, etag = store.read(self.project)
        store.upsert_target(
            self.project,
            provider="gitlab",
            repository="group/repo",
            branch="main",
            expected_etag=etag,
        )
        return store

    def test_target_connection_pass_creates_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store_with_target(Path(tmp))
            evidence = FakeEvidence()

            class Adapter:
                def live_state(self, repository, branch):
                    return {
                        "provider": "gitlab",
                        "repository": {
                            "full_name": repository,
                            "default_branch": "main",
                        },
                        "branch": {
                            "name": branch,
                            "head_sha": "abc123",
                        },
                    }

            with (
                patch.object(
                    server,
                    "project_by_id",
                    return_value=self.project,
                ),
                patch.object(
                    server,
                    "PROVIDER_BINDING_STORE",
                    store,
                ),
                patch.object(
                    server,
                    "provider_adapter",
                    return_value=Adapter(),
                ),
                patch.object(server, "EVIDENCE_STORE", evidence),
            ):
                result = server.test_provider_connection(
                    "P-1",
                    "gitlab",
                )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["head_sha"], "abc123")
            self.assertEqual(
                evidence.evidence[0]["evidence_type"],
                "PROVIDER_CONNECTIVITY",
            )
            self.assertEqual(
                evidence.events[0]["event_type"],
                "PROVIDER_CONNECTIVITY_PASSED",
            )

    def test_provider_read_failure_is_visible_and_evidenced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = self._store_with_target(Path(tmp))
            evidence = FakeEvidence()

            class Adapter:
                def live_state(self, repository, branch):
                    raise ProviderError("simulated")

            with (
                patch.object(
                    server,
                    "project_by_id",
                    return_value=self.project,
                ),
                patch.object(
                    server,
                    "PROVIDER_BINDING_STORE",
                    store,
                ),
                patch.object(
                    server,
                    "provider_adapter",
                    return_value=Adapter(),
                ),
                patch.object(server, "EVIDENCE_STORE", evidence),
            ):
                result = server.test_provider_connection(
                    "P-1",
                    "gitlab",
                )

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(
                result["errors"],
                ["PROVIDER_READ_FAILED"],
            )
            self.assertEqual(
                evidence.events[0]["event_type"],
                "PROVIDER_CONNECTIVITY_FAILED",
            )

    def test_unbound_target_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ProviderBindingStore(Path(tmp))
            with (
                patch.object(
                    server,
                    "project_by_id",
                    return_value=self.project,
                ),
                patch.object(
                    server,
                    "PROVIDER_BINDING_STORE",
                    store,
                ),
                patch.object(server, "provider_adapter") as adapter,
            ):
                result = server.test_provider_connection(
                    "P-1",
                    "gitlab",
                )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                result["errors"],
                ["PROVIDER_BINDING_NOT_CONFIGURED"],
            )
            adapter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
