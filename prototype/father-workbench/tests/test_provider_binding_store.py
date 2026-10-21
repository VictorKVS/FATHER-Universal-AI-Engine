from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from provider_binding_store import (
    BindingConflictError,
    ProviderBindingStore,
)
from migration_verifier import verify_provider_parity, verify_ref_inventory


class RefParityTests(unittest.TestCase):
    def test_complete_equal_inventory_passes(self) -> None:
        report = verify_ref_inventory(
            project_id="P-1",
            source={
                "provider": "github",
                "repository": "owner/repo",
                "default_branch": "main",
                "branches": {"main": "a", "feature/x": "b"},
                "tags": {"v1": "a"},
                "complete": True,
                "limitations": [],
            },
            target={
                "provider": "gitlab",
                "repository": "group/repo",
                "default_branch": "main",
                "branches": {"main": "a", "feature/x": "b"},
                "tags": {"v1": "a"},
                "complete": True,
                "limitations": [],
            },
        )
        self.assertEqual(report["state"], "PASS")
        self.assertEqual(report["blockers"], [])

    def test_incomplete_or_mismatched_inventory_fails(self) -> None:
        report = verify_ref_inventory(
            project_id="P-1",
            source={
                "provider": "github",
                "repository": "owner/repo",
                "default_branch": "main",
                "branches": {"main": "a"},
                "tags": {"v1": "a"},
                "complete": True,
                "limitations": [],
            },
            target={
                "provider": "sourcecraft",
                "repository": "group/repo",
                "default_branch": "main",
                "branches": {"main": "b"},
                "tags": {},
                "complete": False,
                "limitations": ["TAG_INVENTORY_API_NOT_VERIFIED"],
            },
        )
        self.assertEqual(report["state"], "FAIL")
        self.assertIn("TARGET_REF_INVENTORY_INCOMPLETE", report["blockers"])
        self.assertIn("BRANCH_SHA_MISMATCH", report["blockers"])
        self.assertIn("TARGET_MISSING_TAGS", report["blockers"])


class ProviderBindingStoreTests(unittest.TestCase):
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

    def test_target_binding_is_tracked_with_etag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ProviderBindingStore(Path(tmp))
            _state, etag = store.read(self.project)
            state, new_etag = store.upsert_target(
                self.project,
                provider="gitlab",
                repository="group/repo",
                branch="main",
                expected_etag=etag,
            )
            self.assertNotEqual(etag, new_etag)
            self.assertEqual(state["targets"][0]["provider"], "gitlab")

            with self.assertRaises(BindingConflictError):
                store.upsert_target(
                    self.project,
                    provider="gitverse",
                    repository="group/repo",
                    branch="main",
                    expected_etag=etag,
                )

    def test_switch_primary_preserves_previous_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ProviderBindingStore(Path(tmp))
            _state, etag = store.read(self.project)
            state, target_etag = store.upsert_target(
                self.project,
                provider="gitlab",
                repository="group/repo",
                branch="main",
                expected_etag=etag,
            )
            self.assertEqual(state["primary"]["provider"], "github")

            switched, new_etag, historical = store.switch_primary(
                self.project,
                target_provider="gitlab",
                expected_etag=target_etag,
                approval_id="CUTOVER-1",
                verification_refs={"refs": "EVD-REF"},
            )

            self.assertNotEqual(target_etag, new_etag)
            self.assertEqual(switched["primary"]["provider"], "gitlab")
            self.assertEqual(switched["primary"]["repository"], "group/repo")
            self.assertEqual(len(switched["targets"]), 1)
            self.assertEqual(
                switched["targets"][0]["provider"],
                "github",
            )
            self.assertEqual(
                switched["targets"][0]["status"],
                "ROLLBACK_CANDIDATE",
            )
            self.assertEqual(historical["provider"], "github")
            self.assertEqual(switched["historical"][-1]["provider"], "github")
            self.assertEqual(
                switched["last_switch"]["approval_id"],
                "CUTOVER-1",
            )

    def test_target_cannot_equal_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ProviderBindingStore(Path(tmp))
            _state, etag = store.read(self.project)
            with self.assertRaises(ValueError):
                store.upsert_target(
                    self.project,
                    provider="github",
                    repository="owner/repo2",
                    branch="main",
                    expected_etag=etag,
                )


class MigrationVerifierTests(unittest.TestCase):
    def test_equal_branch_and_sha_pass(self) -> None:
        report = verify_provider_parity(
            project_id="P-1",
            source={
                "provider": "github",
                "repository": {"full_name": "owner/repo"},
                "branch": {"name": "main", "head_sha": "abc"},
            },
            target={
                "provider": "gitlab",
                "repository": {"full_name": "group/repo"},
                "branch": {"name": "main", "head_sha": "abc"},
            },
        )
        self.assertEqual(report["state"], "PASS")
        self.assertTrue(report["checks"]["head_sha_parity"])

    def test_head_mismatch_fails(self) -> None:
        report = verify_provider_parity(
            project_id="P-1",
            source={
                "provider": "github",
                "repository": {"full_name": "owner/repo"},
                "branch": {"name": "main", "head_sha": "abc"},
            },
            target={
                "provider": "gitlab",
                "repository": {"full_name": "group/repo"},
                "branch": {"name": "main", "head_sha": "def"},
            },
        )
        self.assertEqual(report["state"], "FAIL")
        self.assertIn("HEAD_SHA_MISMATCH", report["blockers"])


if __name__ == "__main__":
    unittest.main()
