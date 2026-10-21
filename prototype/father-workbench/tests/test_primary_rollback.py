from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import server
from provider_binding_store import ProviderBindingStore


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


class PrimaryRollbackTests(unittest.TestCase):
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

    def prepare_switched_store(self, root: Path):
        store = ProviderBindingStore(root)
        _state, etag = store.read(self.project)
        _state, target_etag = store.upsert_target(
            self.project,
            provider="gitlab",
            repository="group/repo",
            branch="main",
            expected_etag=etag,
        )
        state, switched_etag, _historical = store.switch_primary(
            self.project,
            target_provider="gitlab",
            expected_etag=target_etag,
            approval_id="CUTOVER-1",
            verification_refs={"refs": "EVD-REFS"},
        )
        self.assertEqual(state["primary"]["provider"], "gitlab")
        rollback = next(
            item
            for item in state["targets"]
            if item.get("status") == "ROLLBACK_CANDIDATE"
        )
        self.assertEqual(rollback["provider"], "github")
        return store, switched_etag

    def test_rollback_restores_preserved_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store, switched_etag = self.prepare_switched_store(Path(tmp))
            evidence = FakeEvidence()
            audit = []

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
                patch.object(server, "EVIDENCE_STORE", evidence),
                patch.object(
                    server,
                    "write_audit_event",
                    side_effect=audit.append,
                ),
                patch.object(
                    server,
                    "test_provider_connection",
                    return_value={
                        "status": "PASS",
                        "evidence": {
                            "evidence_id": "EVD-CONNECT"
                        },
                    },
                ),
                patch.object(
                    server,
                    "live_binding_state",
                    return_value={
                        "provider": "github",
                        "repository": {
                            "full_name": "owner/repo"
                        },
                        "branch": {
                            "name": "main",
                            "head_sha": "abc123",
                        },
                        "workflow_runs": [],
                        "change_requests": [],
                    },
                ),
                patch.object(
                    server,
                    "capture_live_provider_evidence",
                    return_value={
                        "evidence_id": "EVD-ROLLBACK-LIVE",
                        "deduplicated": False,
                    },
                ),
            ):
                result = server.rollback_primary_provider(
                    "P-1",
                    "github",
                    switched_etag,
                )

            self.assertEqual(result["status"], "ROLLED_BACK")
            self.assertEqual(
                result["primary"]["provider"],
                "github",
            )
            self.assertEqual(
                result["previous_primary"]["provider"],
                "gitlab",
            )
            self.assertEqual(
                [item["status"] for item in audit],
                ["EXECUTING", "ROLLED_BACK"],
            )
            state, _etag = store.read(self.project)
            self.assertEqual(
                state["primary"]["provider"],
                "github",
            )
            self.assertTrue(
                any(
                    item["event_type"]
                    == "PROVIDER_PRIMARY_ROLLED_BACK"
                    for item in evidence.events
                )
            )

    def test_rollback_blocks_when_candidate_is_not_accessible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store, switched_etag = self.prepare_switched_store(Path(tmp))

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
                    "test_provider_connection",
                    return_value={
                        "status": "FAIL",
                        "errors": ["PROVIDER_READ_FAILED"],
                    },
                ),
            ):
                result = server.rollback_primary_provider(
                    "P-1",
                    "github",
                    switched_etag,
                )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                result["errors"],
                ["ROLLBACK_TARGET_CONNECTIVITY_NOT_PASS"],
            )
            state, _etag = store.read(self.project)
            self.assertEqual(state["primary"]["provider"], "gitlab")

    def test_rollback_rejects_stale_binding_etag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store, switched_etag = self.prepare_switched_store(Path(tmp))
            state, current_etag = store.read(self.project)
            store.upsert_target(
                self.project,
                provider="bitbucket",
                repository="team/repo",
                branch="main",
                expected_etag=current_etag,
            )

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
            ):
                result = server.rollback_primary_provider(
                    "P-1",
                    "github",
                    switched_etag,
                )

            self.assertEqual(result["status"], "CONFLICT")
            self.assertEqual(
                result["errors"],
                ["BINDING_ETAG_CONFLICT"],
            )


if __name__ == "__main__":
    unittest.main()
