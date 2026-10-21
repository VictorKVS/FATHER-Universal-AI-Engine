from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from project_health import assess_project_health


class ProjectHealthTests(unittest.TestCase):
    def base_project(self):
        return {
            "project_id": "P-1",
            "pre_design_gate": "PASS",
            "architecture_gate": "PASS",
            "security_gate": "PASS",
            "runtime_status": "PRODUCTION_PROVEN",
        }

    def base_state(self):
        return {
            "current_stage": "OPS",
            "document_summary": {"done": 10, "total": 10},
            "evidence_status": "PASS",
            "stages": [
                {
                    "id": "OPS",
                    "gate": "PASS",
                }
            ],
        }

    def base_bindings(self):
        return {
            "primary": {
                "provider": "github",
                "repository": "owner/repo",
                "branch": "main",
            },
            "last_switch_health": {
                "status": "PASS",
                "blockers": [],
                "rollback_recommended": False,
            },
        }

    def test_release_ready_requires_all_hard_prerequisites(self):
        result = assess_project_health(
            project=self.base_project(),
            state=self.base_state(),
            bindings=self.base_bindings(),
            devsecops={
                "status": "PASS",
                "head_sha": "abc",
                "blockers": [],
            },
            evidence_count=8,
        )
        self.assertEqual(result["overall"], "RELEASE_READY")
        self.assertTrue(result["release_ready"])
        self.assertEqual(result["hard_blockers"], [])

    def test_provider_degradation_blocks_release(self):
        bindings = self.base_bindings()
        bindings["last_switch_health"] = {
            "status": "DEGRADED",
            "blockers": ["POST_CUTOVER_REF_PARITY_FAILED"],
            "rollback_recommended": True,
        }
        result = assess_project_health(
            project=self.base_project(),
            state=self.base_state(),
            bindings=bindings,
            devsecops={
                "status": "PASS",
                "head_sha": "abc",
                "blockers": [],
            },
            evidence_count=8,
        )
        self.assertEqual(result["overall"], "BLOCKED")
        self.assertFalse(result["release_ready"])
        self.assertIn(
            "PROVIDER:POST_CUTOVER_REF_PARITY_FAILED",
            result["hard_blockers"],
        )

    def test_unknown_devsecops_does_not_fake_release_ready(self):
        result = assess_project_health(
            project=self.base_project(),
            state=self.base_state(),
            bindings=self.base_bindings(),
            devsecops=None,
            evidence_count=0,
        )
        self.assertEqual(result["overall"], "IN_PROGRESS")
        self.assertFalse(result["release_ready"])
        self.assertEqual(
            result["dimensions"]["devsecops"]["status"],
            "UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
