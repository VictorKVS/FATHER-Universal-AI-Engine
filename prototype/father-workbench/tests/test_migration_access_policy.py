from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from migration_access_policy import evaluate_access_policy


class MigrationAccessPolicyTests(unittest.TestCase):
    def test_weaker_target_is_blocked(self) -> None:
        report = evaluate_access_policy(
            project_id="P-1",
            source={
                "provider": "github",
                "repository": "owner/repo",
                "branch": "main",
                "complete": True,
                "protected": True,
                "force_push_allowed": False,
                "deletion_allowed": False,
                "review_required": True,
                "code_owner_review_required": True,
                "required_status_checks": True,
                "limitations": [],
            },
            target={
                "provider": "gitlab",
                "repository": "group/repo",
                "branch": "main",
                "complete": True,
                "protected": True,
                "force_push_allowed": True,
                "deletion_allowed": False,
                "review_required": None,
                "code_owner_review_required": False,
                "required_status_checks": None,
                "limitations": [],
            },
        )
        self.assertEqual(report["state"], "FAIL")
        self.assertIn("TARGET_FORCE_PUSH_WEAKER", report["blockers"])
        self.assertIn("TARGET_REVIEW_POLICY_UNKNOWN", report["blockers"])
        self.assertIn(
            "TARGET_CODE_OWNER_POLICY_WEAKER_OR_UNKNOWN",
            report["blockers"],
        )

    def test_known_non_weaker_policy_still_requires_cross_provider_review(self) -> None:
        base = {
            "complete": True,
            "protected": True,
            "force_push_allowed": False,
            "deletion_allowed": False,
            "review_required": False,
            "code_owner_review_required": False,
            "required_status_checks": False,
            "limitations": [],
        }
        report = evaluate_access_policy(
            project_id="P-1",
            source={"provider": "github", "repository": "a/b", "branch": "main", **base},
            target={"provider": "gitlab", "repository": "c/d", "branch": "main", **base},
        )
        self.assertEqual(report["state"], "PASS_WITH_REVIEW")
        self.assertIn(
            "CROSS_PROVIDER_SECURITY_REVIEW_REQUIRED",
            report["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
