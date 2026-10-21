from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from provider_binding_store import (
    BindingConflictError,
    ProviderBindingStore,
)
from migration_verifier import verify_provider_parity


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
