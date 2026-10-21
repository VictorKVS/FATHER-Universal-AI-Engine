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
from migration_security_review_store import MigrationSecurityReviewStore


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
            _initial, etag = binding_store.read(self.project)

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
                def __init__(self, provider, repository):
                    self.provider = provider
                    self.repository = repository

                def split_repository(self, repository):
                    return tuple(repository.split("/"))

                def validate_branch_name(self, branch):
                    return branch

                def live_state(self, repository, branch):
                    return {
                        "provider": self.provider,
                        "repository": {"full_name": repository},
                        "branch": {
                            "name": branch,
                            "head_sha": "abc123",
                        },
                    }

                def ref_inventory(self, repository):
                    return {
                        "provider": self.provider,
                        "repository": repository,
                        "default_branch": "main",
                        "branches": {"main": "abc123"},
                        "tags": {},
                        "complete": True,
                        "limitations": [],
                    }

                def access_policy(self, repository, branch):
                    return {
                        "provider": self.provider,
                        "repository": repository,
                        "branch": branch,
                        "complete": True,
                        "protected": True,
                        "force_push_allowed": False,
                        "deletion_allowed": False,
                        "review_required": False,
                        "code_owner_review_required": False,
                        "required_status_checks": False,
                        "admin_enforcement": False,
                        "direct_push_restricted": True,
                        "limitations": [],
                    }

            def adapter_for(provider):
                repository = (
                    "owner/repo"
                    if provider == "github"
                    else "group/repo"
                )
                return FakeAdapter(provider, repository)

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(
                    server,
                    "provider_config_by_id",
                    return_value={"id": "gitlab"},
                ),
                patch.object(
                    server,
                    "provider_adapter",
                    side_effect=adapter_for,
                ),
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

                verified = server.verify_migration_target(
                    "P-1",
                    "gitlab",
                )

            self.assertEqual(verified["status"], "PASS")
            self.assertTrue(verified["branch_parity_proven"])
            self.assertTrue(verified["full_ref_parity_proven"])
            self.assertFalse(verified["switch_primary_eligible"])
            self.assertIn(
                "MIGRATION_SECURITY_REVIEW_REQUIRED",
                verified["switch_primary_blockers"],
            )
            self.assertTrue(
                verified["verification"]["checks"]["head_sha_parity"]
            )
            self.assertEqual(len(evidence), 3)
            self.assertEqual(
                {item["evidence_type"] for item in evidence},
                {
                    "MIGRATION_VERIFICATION",
                    "REF_PARITY_REPORT",
                    "ACCESS_AND_BRANCH_POLICY_REPORT",
                },
            )
            self.assertTrue(verified["access_policy_not_weaker"])
            self.assertTrue(verified["security_review_required"])
            self.assertTrue(
                any(
                    event["event_type"] == "MIGRATION_REF_PARITY_PASSED"
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

            class FakeAdapter:
                def __init__(self, provider):
                    self.provider = provider

                def live_state(self, repository, branch):
                    sha = "abc" if self.provider == "github" else "def"
                    return {
                        "provider": self.provider,
                        "repository": {"full_name": repository},
                        "branch": {"name": branch, "head_sha": sha},
                    }

                def ref_inventory(self, repository):
                    sha = "abc" if self.provider == "github" else "def"
                    return {
                        "provider": self.provider,
                        "repository": repository,
                        "default_branch": "main",
                        "branches": {"main": sha},
                        "tags": {},
                        "complete": True,
                        "limitations": [],
                    }

                def access_policy(self, repository, branch):
                    return {
                        "provider": self.provider,
                        "repository": repository,
                        "branch": branch,
                        "complete": True,
                        "protected": True,
                        "force_push_allowed": False,
                        "deletion_allowed": False,
                        "review_required": False,
                        "code_owner_review_required": False,
                        "required_status_checks": False,
                        "admin_enforcement": False,
                        "direct_push_restricted": True,
                        "limitations": [],
                    }

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", binding_store),
                patch.object(server, "EVIDENCE_STORE", FakeEvidence()),
                patch.object(
                    server,
                    "provider_adapter",
                    side_effect=lambda provider: FakeAdapter(provider),
                ),
            ):
                result = server.verify_migration_target("P-1", "gitlab")

            self.assertEqual(result["status"], "FAIL")
            self.assertFalse(result["switch_primary_eligible"])
            self.assertIn(
                "HEAD_SHA_MISMATCH",
                result["verification"]["blockers"],
            )
            self.assertIn(
                "BRANCH_SHA_MISMATCH",
                result["ref_parity"]["blockers"],
            )


    def test_security_approval_requires_current_pass_and_is_tracked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review_store = MigrationSecurityReviewStore(Path(tmp))
            _state, etag = review_store.read("P-1")

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

            verification = {
                "status": "PASS",
                "verification": {"verification_id": "MIGVERIFY-1"},
                "ref_parity": {"report_id": "REFPARITY-1"},
                "access_policy": {"report_id": "ACCESSPOL-1"},
                "evidence": {
                    "branch": {"evidence_id": "EVD-BRANCH"},
                    "refs": {"evidence_id": "EVD-REFS"},
                    "access_policy": {"evidence_id": "EVD-ACCESS"},
                },
            }

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value=verification,
                ),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    review_store,
                ),
                patch.object(server, "EVIDENCE_STORE", FakeEvidence()),
            ):
                result = server.review_migration_security(
                    "P-1",
                    "gitlab",
                    "APPROVE",
                    (
                        "Current branch, ref and access-policy evidence is "
                        "acceptable for migration security review."
                    ),
                    "Information Security Specialist",
                    etag,
                )

            self.assertEqual(result["status"], "APPLIED")
            self.assertEqual(result["decision"], "APPROVE")
            self.assertFalse(result["cutover_eligible"])
            self.assertEqual(
                result["cutover_blockers"],
                ["CUTOVER_APPROVAL_REQUIRED"],
            )
            self.assertEqual(
                evidence[0]["evidence_type"],
                "MIGRATION_SECURITY_REVIEW",
            )
            latest = review_store.latest_for_target("P-1", "gitlab")
            self.assertEqual(latest["decision"], "APPROVE")

    def test_security_approve_is_blocked_when_parity_is_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review_store = MigrationSecurityReviewStore(Path(tmp))
            _state, etag = review_store.read("P-1")

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value={
                        "status": "FAIL",
                        "verification": {
                            "blockers": ["HEAD_SHA_MISMATCH"]
                        },
                    },
                ),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    review_store,
                ),
            ):
                result = server.review_migration_security(
                    "P-1",
                    "gitlab",
                    "APPROVE",
                    (
                        "Approval must not proceed because current parity "
                        "evidence is not valid."
                    ),
                    "Information Security Specialist",
                    etag,
                )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn(
                "TECHNICAL_MIGRATION_EVIDENCE_NOT_PASS",
                result["errors"],
            )


if __name__ == "__main__":
    unittest.main()
