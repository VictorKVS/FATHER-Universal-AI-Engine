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


class MigrationControlPlaneTests(unittest.TestCase):
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

    def test_binding_update_requires_registered_provider(self) -> None:
        with patch.object(server, "project_by_id", return_value=self.project):
            result = server.upsert_provider_binding(
                "P-1",
                "does-not-exist",
                "group/repo",
                "main",
                "etag",
            )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["errors"], ["PROVIDER_NOT_REGISTERED"])

    def test_binding_and_parity_pass_create_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            binding_store = ProviderBindingStore(Path(tmp))
            initial, etag = binding_store.read(self.project)
            del initial

            events = []
            evidence = []

            class FakeEvidence:
                def append_manufacturing_event(self, **kwargs):
                    item = {
                        "event_id": f"MFG-{len(events)+1}",
                        **kwargs,
                    }
                    events.append(item)
                    return item

                def store_evidence(self, **kwargs):
                    item = {
                        "evidence_id": f"EVD-{len(evidence)+1}",
                        "deduplicated": False,
                        **kwargs,
                    }
                    evidence.append(item)
                    return item

            class FakeAdapter:
                def split_repository(self, repository):
                    return tuple(repository.split("/"))

                def validate_branch_name(self, branch):
                    return branch

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(
                    server,
                    "provider_config_by_id",
                    return_value={"id": "gitlab"},
                ),
                patch.object(server, "provider_adapter", return_value=FakeAdapter()),
                patch.object(server, "PROVIDER_BINDING_STORE", binding_store),
                patch.object(server, "EVIDENCE_STORE", FakeEvidence()),
            ):
                bound = server.upsert_provider_binding(
                    "P-1",
                    "gitlab",
                    "group/repo",
                    "main",
                    etag,
                )
                self.assertEqual(bound["status"], "APPLIED")

                source = {
                    "provider": "github",
                    "repository": {"full_name": "owner/repo"},
                    "branch": {"name": "main", "head_sha": "abc123"},
                }
                target = {
                    "provider": "gitlab",
                    "repository": {"full_name": "group/repo"},
                    "branch": {"name": "main", "head_sha": "abc123"},
                }
                with (
                    patch.object(
                        server,
                        "live_provider_state",
                        return_value=source,
                    ),
                    patch.object(
                        server,
                        "live_binding_state",
                        return_value=target,
                    ),
                ):
                    verified = server.verify_migration_target(
                        "P-1",
                        "gitlab",
                    )

            self.assertEqual(verified["status"], "PASS")
            self.assertTrue(verified["branch_parity_proven"])
            self.assertFalse(verified["switch_primary_eligible"])
            self.assertIn(
                "FULL_REF_PARITY_REQUIRED",
                verified["switch_primary_blockers"],
            )
            self.assertEqual(
                verified["verification"]["checks"]["head_sha_parity"],
                True,
            )
            self.assertEqual(len(evidence), 1)
            self.assertEqual(
                evidence[0]["evidence_type"],
                "MIGRATION_VERIFICATION",
            )
            self.assertTrue(
                any(
                    event["event_type"] == "MIGRATION_VERIFICATION_PASSED"
                    for event in events
                )
            )

    def test_parity_mismatch_does_not_allow_switch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            binding_store = ProviderBindingStore(Path(tmp))
            _state, etag = binding_store.read(self.project)
            binding_store.upsert_target(
                self.project,
                provider="gitlab",
                repository="group/repo",
                branch="main",
                expected_etag=etag,
            )

            class FakeEvidence:
                def append_manufacturing_event(self, **kwargs):
                    return {"event_id": "MFG-1", **kwargs}

                def store_evidence(self, **kwargs):
                    return {
                        "evidence_id": "EVD-1",
                        "deduplicated": False,
                        **kwargs,
                    }

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", binding_store),
                patch.object(server, "EVIDENCE_STORE", FakeEvidence()),
                patch.object(
                    server,
                    "live_provider_state",
                    return_value={
                        "provider": "github",
                        "repository": {"full_name": "owner/repo"},
                        "branch": {"name": "main", "head_sha": "abc"},
                    },
                ),
                patch.object(
                    server,
                    "live_binding_state",
                    return_value={
                        "provider": "gitlab",
                        "repository": {"full_name": "group/repo"},
                        "branch": {"name": "main", "head_sha": "def"},
                    },
                ),
            ):
                result = server.verify_migration_target("P-1", "gitlab")

            self.assertEqual(result["status"], "FAIL")
            self.assertFalse(result["switch_primary_eligible"])
            self.assertIn(
                "HEAD_SHA_MISMATCH",
                result["verification"]["blockers"],
            )


if __name__ == "__main__":
    unittest.main()
