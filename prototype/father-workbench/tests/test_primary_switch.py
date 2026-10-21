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
from migration_cutover_store import MigrationCutoverStore
from migration_security_review_store import MigrationSecurityReviewStore
from provider_binding_store import ProviderBindingStore


class FakeEvidence:
    def __init__(self) -> None:
        self.events = []
        self.evidence = []

    def append_manufacturing_event(self, **kwargs):
        item = {
            "event_id": f"MFG-{len(self.events)+1}",
            **kwargs,
        }
        self.events.append(item)
        return item

    def store_evidence(self, **kwargs):
        item = {
            "evidence_id": f"EVD-SWITCH-{len(self.evidence)+1}",
            "deduplicated": False,
            **kwargs,
        }
        self.evidence.append(item)
        return item


def current_verification():
    return {
        "status": "PASS",
        "verification": {"verification_id": "MIGVERIFY-CURRENT"},
        "ref_parity": {"report_id": "REFPARITY-CURRENT"},
        "access_policy": {"report_id": "ACCESSPOL-CURRENT"},
        "evidence": {
            "branch": {"evidence_id": "EVD-BRANCH-CURRENT"},
            "refs": {"evidence_id": "EVD-REFS-CURRENT"},
            "access_policy": {"evidence_id": "EVD-ACCESS-CURRENT"},
        },
    }


def current_refs():
    return {
        "branch": "EVD-BRANCH-CURRENT",
        "refs": "EVD-REFS-CURRENT",
        "access": "EVD-ACCESS-CURRENT",
        "verification_id": "MIGVERIFY-CURRENT",
        "ref_parity_report_id": "REFPARITY-CURRENT",
        "access_policy_report_id": "ACCESSPOL-CURRENT",
    }


class PostCutoverVerificationTests(unittest.TestCase):
    def _adapter(self, provider: str, ref_sha: str):
        class Adapter:
            def live_state(self, repository, branch):
                return {
                    "provider": provider,
                    "repository": {"full_name": repository},
                    "branch": {
                        "name": branch,
                        "head_sha": "abc123",
                    },
                }

            def ref_inventory(self, repository):
                return {
                    "provider": provider,
                    "repository": repository,
                    "default_branch": "main",
                    "branches": {"main": ref_sha},
                    "tags": {"v1": ref_sha},
                    "complete": True,
                    "limitations": [],
                }

            def access_policy(self, repository, branch):
                return {
                    "provider": provider,
                    "repository": repository,
                    "branch": branch,
                    "complete": True,
                    "protected": True,
                    "force_push_allowed": False,
                    "deletion_allowed": False,
                    "review_required": True,
                    "code_owner_review_required": False,
                    "required_status_checks": True,
                    "admin_enforcement": True,
                    "direct_push_restricted": True,
                    "limitations": [],
                }

        return Adapter()

    def test_full_post_cutover_parity_passes(self) -> None:
        evidence = FakeEvidence()

        def adapter(provider):
            return self._adapter(provider, "abc123")

        with (
            patch.object(
                server,
                "provider_adapter",
                side_effect=adapter,
            ),
            patch.object(server, "EVIDENCE_STORE", evidence),
        ):
            result = server.verify_post_cutover(
                "P-1",
                {
                    "provider": "github",
                    "repository": "owner/repo",
                    "branch": "main",
                },
                {
                    "provider": "gitlab",
                    "repository": "group/repo",
                    "branch": "main",
                },
                "ACT-1",
            )

        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["rollback_recommended"])
        self.assertEqual(
            result["ref_parity"]["state"],
            "PASS",
        )
        self.assertEqual(
            result["access_policy"]["state"],
            "PASS_WITH_REVIEW",
        )

    def test_ref_mismatch_recommends_rollback(self) -> None:
        evidence = FakeEvidence()

        def adapter(provider):
            sha = "abc123" if provider == "github" else "def456"
            return self._adapter(provider, sha)

        with (
            patch.object(
                server,
                "provider_adapter",
                side_effect=adapter,
            ),
            patch.object(server, "EVIDENCE_STORE", evidence),
        ):
            result = server.verify_post_cutover(
                "P-1",
                {
                    "provider": "github",
                    "repository": "owner/repo",
                    "branch": "main",
                },
                {
                    "provider": "gitlab",
                    "repository": "group/repo",
                    "branch": "main",
                },
                "ACT-2",
            )

        self.assertEqual(result["status"], "DEGRADED")
        self.assertTrue(result["rollback_recommended"])
        self.assertIn(
            "POST_CUTOVER_REF_PARITY_FAILED",
            result["blockers"],
        )


class PrimarySwitchTests(unittest.TestCase):
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

    def prepare_stores(
        self,
        root: Path,
        *,
        approval_refs=None,
    ):
        bindings = ProviderBindingStore(root)
        security = MigrationSecurityReviewStore(root)
        cutover = MigrationCutoverStore(root)

        _state, binding_etag = bindings.read(self.project)
        _bound, target_etag = bindings.upsert_target(
            self.project,
            provider="gitlab",
            repository="group/repo",
            branch="main",
            expected_etag=binding_etag,
        )

        refs = approval_refs or current_refs()

        _review_state, review_etag = security.read("P-1")
        review, _ = security.append_review(
            project_id="P-1",
            target_provider="gitlab",
            decision="APPROVE",
            rationale=(
                "Current migration parity and access evidence is accepted "
                "for the provider cutover security review."
            ),
            reviewed_by="Information Security Specialist",
            verification_refs=refs,
            expected_etag=review_etag,
        )

        _cutover_state, cutover_etag = cutover.read("P-1")
        approval, _ = cutover.append(
            project_id="P-1",
            target_provider="gitlab",
            decision="APPROVE",
            rationale=(
                "Provider cutover is approved against the current verified "
                "migration and security evidence."
            ),
            approved_by="Project Owner",
            security_review_id=review["review_id"],
            verification_refs=refs,
            expected_etag=cutover_etag,
        )
        return bindings, security, cutover, target_etag, approval

    def test_switch_primary_requires_fresh_approved_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                bindings,
                security,
                cutover,
                target_etag,
                approval,
            ) = self.prepare_stores(root)

            evidence = FakeEvidence()
            audit = []

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", bindings),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    security,
                ),
                patch.object(server, "MIGRATION_CUTOVER_STORE", cutover),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value=current_verification(),
                ),
                patch.object(server, "EVIDENCE_STORE", evidence),
                patch.object(
                    server,
                    "write_audit_event",
                    side_effect=audit.append,
                ),
                patch.object(
                    server,
                    "live_binding_state",
                    return_value={
                        "provider": "gitlab",
                        "repository": {"full_name": "group/repo"},
                        "branch": {"name": "main", "head_sha": "abc123"},
                        "workflow_runs": [],
                        "change_requests": [],
                    },
                ),
                patch.object(
                    server,
                    "verify_post_cutover",
                    return_value={
                        "status": "PASS",
                        "blockers": [],
                        "rollback_recommended": False,
                        "evidence": {
                            "evidence_id": "EVD-POST-CUTOVER-VERIFY"
                        },
                    },
                ),
                patch.object(
                    server,
                    "capture_live_provider_evidence",
                    return_value={
                        "evidence_id": "EVD-POST-CUTOVER",
                        "deduplicated": False,
                    },
                ),
            ):
                result = server.switch_primary_provider(
                    "P-1",
                    "gitlab",
                    target_etag,
                )

            self.assertEqual(result["status"], "APPLIED")
            self.assertEqual(result["primary"]["provider"], "gitlab")
            self.assertEqual(
                result["previous_primary"]["provider"],
                "github",
            )
            self.assertTrue(result["rollback_binding_preserved"])
            self.assertEqual(result["post_cutover_status"], "PASS")
            self.assertFalse(result["rollback_recommended"])
            self.assertEqual(
                result["cutover_approval_id"],
                approval["approval_id"],
            )
            self.assertEqual(
                [item["status"] for item in audit],
                ["EXECUTING", "SUCCEEDED"],
            )

            state, _etag = bindings.read(self.project)
            self.assertEqual(state["primary"]["provider"], "gitlab")
            self.assertEqual(state["historical"][-1]["provider"], "github")
            with patch.object(
                server,
                "PROVIDER_BINDING_STORE",
                bindings,
            ):
                self.assertEqual(
                    server.active_provider_binding(self.project)["provider"],
                    "gitlab",
                )
            self.assertTrue(
                any(
                    item["event_type"] == "PROVIDER_PRIMARY_SWITCHED"
                    for item in evidence.events
                )
            )

    def test_switch_primary_marks_degraded_when_post_cutover_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                bindings,
                security,
                cutover,
                target_etag,
                _approval,
            ) = self.prepare_stores(root)

            evidence = FakeEvidence()
            audit = []

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", bindings),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    security,
                ),
                patch.object(server, "MIGRATION_CUTOVER_STORE", cutover),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value=current_verification(),
                ),
                patch.object(server, "EVIDENCE_STORE", evidence),
                patch.object(
                    server,
                    "write_audit_event",
                    side_effect=audit.append,
                ),
                patch.object(
                    server,
                    "verify_post_cutover",
                    return_value={
                        "status": "DEGRADED",
                        "blockers": [
                            "POST_CUTOVER_REF_PARITY_FAILED"
                        ],
                        "rollback_recommended": True,
                    },
                ),
                patch.object(
                    server,
                    "live_binding_state",
                    return_value={
                        "provider": "gitlab",
                        "repository": {
                            "full_name": "group/repo"
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
                        "evidence_id": "EVD-LIVE",
                        "deduplicated": False,
                    },
                ),
            ):
                result = server.switch_primary_provider(
                    "P-1",
                    "gitlab",
                    target_etag,
                )

            self.assertEqual(
                result["status"],
                "APPLIED_POST_CUTOVER_DEGRADED",
            )
            self.assertEqual(
                result["post_cutover_status"],
                "DEGRADED",
            )
            self.assertTrue(result["rollback_recommended"])
            self.assertIn(
                "POST_CUTOVER_REF_PARITY_FAILED",
                result["post_cutover"]["blockers"],
            )
            state, _etag = bindings.read(self.project)
            self.assertEqual(
                state["primary"]["provider"],
                "gitlab",
            )
            rollback = next(
                item
                for item in state["targets"]
                if item.get("status") == "ROLLBACK_CANDIDATE"
            )
            self.assertEqual(rollback["provider"], "github")

    def test_switch_primary_rejects_stale_cutover_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale_refs = {
                key: "OLD"
                for key in current_refs()
            }
            (
                bindings,
                security,
                cutover,
                target_etag,
                _approval,
            ) = self.prepare_stores(
                root,
                approval_refs=stale_refs,
            )

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", bindings),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    security,
                ),
                patch.object(server, "MIGRATION_CUTOVER_STORE", cutover),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value=current_verification(),
                ),
            ):
                result = server.switch_primary_provider(
                    "P-1",
                    "gitlab",
                    target_etag,
                )

            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(
                result["errors"],
                ["CUTOVER_APPROVAL_STALE"],
            )
            state, _etag = bindings.read(self.project)
            self.assertEqual(state["primary"]["provider"], "github")

    def test_switch_primary_rejects_stale_binding_etag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (
                bindings,
                security,
                cutover,
                target_etag,
                _approval,
            ) = self.prepare_stores(root)

            # Mutate tracked bindings after the caller read target_etag.
            bindings.upsert_target(
                self.project,
                provider="bitbucket",
                repository="team/repo",
                branch="main",
                expected_etag=target_etag,
            )

            with (
                patch.object(server, "project_by_id", return_value=self.project),
                patch.object(server, "PROVIDER_BINDING_STORE", bindings),
                patch.object(
                    server,
                    "MIGRATION_SECURITY_REVIEW_STORE",
                    security,
                ),
                patch.object(server, "MIGRATION_CUTOVER_STORE", cutover),
                patch.object(
                    server,
                    "verify_migration_target",
                    return_value=current_verification(),
                ),
            ):
                result = server.switch_primary_provider(
                    "P-1",
                    "gitlab",
                    target_etag,
                )

            self.assertEqual(result["status"], "CONFLICT")
            self.assertEqual(
                result["errors"],
                ["BINDING_ETAG_CONFLICT"],
            )


if __name__ == "__main__":
    unittest.main()
