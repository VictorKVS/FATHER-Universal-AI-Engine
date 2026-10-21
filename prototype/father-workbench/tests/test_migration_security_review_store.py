from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from migration_security_review_store import (
    MigrationReviewConflictError,
    MigrationSecurityReviewStore,
)


class MigrationSecurityReviewStoreTests(unittest.TestCase):
    def test_review_requires_rationale_and_is_versioned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MigrationSecurityReviewStore(Path(tmp))
            _state, etag = store.read("P-1")
            review, new_etag = store.append_review(
                project_id="P-1",
                target_provider="gitlab",
                decision="APPROVE",
                rationale=(
                    "Ref parity is proven and normalized branch policy "
                    "is not weaker; manual security review completed."
                ),
                reviewed_by="Information Security Specialist",
                verification_refs={
                    "branch": "EVD-1",
                    "refs": "EVD-2",
                    "access": "EVD-3",
                },
                expected_etag=etag,
            )
            self.assertEqual(review["decision"], "APPROVE")
            self.assertNotEqual(etag, new_etag)
            self.assertEqual(
                store.latest_for_target("P-1", "gitlab")["review_id"],
                review["review_id"],
            )

            with self.assertRaises(MigrationReviewConflictError):
                store.append_review(
                    project_id="P-1",
                    target_provider="gitlab",
                    decision="HOLD",
                    rationale="This rationale is sufficiently long for review.",
                    reviewed_by="Security",
                    verification_refs={},
                    expected_etag=etag,
                )

    def test_short_rationale_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MigrationSecurityReviewStore(Path(tmp))
            _state, etag = store.read("P-1")
            with self.assertRaises(ValueError):
                store.append_review(
                    project_id="P-1",
                    target_provider="gitlab",
                    decision="APPROVE",
                    rationale="too short",
                    reviewed_by="Security",
                    verification_refs={},
                    expected_etag=etag,
                )


if __name__ == "__main__":
    unittest.main()
