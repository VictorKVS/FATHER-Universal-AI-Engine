from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from migration_cutover_store import (
    CutoverConflictError,
    MigrationCutoverStore,
)


class MigrationCutoverStoreTests(unittest.TestCase):
    def test_approval_is_tracked_and_versioned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MigrationCutoverStore(Path(tmp))
            _state, etag = store.read("P-1")
            approval, new_etag = store.append(
                project_id="P-1",
                target_provider="gitlab",
                decision="APPROVE",
                rationale=(
                    "Technical parity and security review are current; "
                    "cutover is approved for the controlled switch."
                ),
                approved_by="Project Owner",
                security_review_id="MIGSEC-1",
                verification_refs={
                    "branch": "EVD-1",
                    "refs": "EVD-2",
                    "access": "EVD-3",
                },
                expected_etag=etag,
            )
            self.assertEqual(approval["decision"], "APPROVE")
            self.assertNotEqual(etag, new_etag)
            self.assertEqual(
                store.latest_for_target("P-1", "gitlab")["approval_id"],
                approval["approval_id"],
            )

            with self.assertRaises(CutoverConflictError):
                store.append(
                    project_id="P-1",
                    target_provider="gitlab",
                    decision="HOLD",
                    rationale="A sufficiently long hold rationale for cutover.",
                    approved_by="Project Owner",
                    security_review_id="",
                    verification_refs={},
                    expected_etag=etag,
                )

    def test_approval_requires_security_review_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MigrationCutoverStore(Path(tmp))
            _state, etag = store.read("P-1")
            with self.assertRaises(ValueError):
                store.append(
                    project_id="P-1",
                    target_provider="gitlab",
                    decision="APPROVE",
                    rationale=(
                        "Cutover rationale is long enough but security "
                        "review is intentionally absent."
                    ),
                    approved_by="Project Owner",
                    security_review_id="",
                    verification_refs={},
                    expected_etag=etag,
                )


if __name__ == "__main__":
    unittest.main()
