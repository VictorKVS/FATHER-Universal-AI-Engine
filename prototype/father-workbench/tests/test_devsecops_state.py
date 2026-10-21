from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from devsecops_state import evaluate_devsecops_state


class DevSecOpsStateTests(unittest.TestCase):
    def test_pass_requires_current_head_success_and_artifact(self) -> None:
        live = {
            "branch": {"head_sha": "abc123"},
            "workflow_runs": [
                {
                    "id": 9,
                    "head_sha": "abc123",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
            "artifacts": [
                {
                    "id": 55,
                    "name": "father-devsecops-abc123",
                    "expired": False,
                    "workflow_run_id": 9,
                }
            ],
        }
        result = evaluate_devsecops_state(live)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["ci_current_head"], "PASS")
        self.assertEqual(result["evidence_artifact"], "PRESENT")

    def test_old_green_run_does_not_pass_new_head(self) -> None:
        live = {
            "branch": {"head_sha": "new123"},
            "workflow_runs": [
                {
                    "id": 9,
                    "head_sha": "old123",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
            "artifacts": [
                {
                    "id": 55,
                    "name": "father-devsecops-old123",
                    "expired": False,
                    "workflow_run_id": 9,
                }
            ],
        }
        result = evaluate_devsecops_state(live)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("CURRENT_HEAD_WORKFLOW_NOT_FOUND", result["blockers"])

    def test_success_without_artifact_is_blocked(self) -> None:
        live = {
            "branch": {"head_sha": "abc123"},
            "workflow_runs": [
                {
                    "id": 9,
                    "head_sha": "abc123",
                    "status": "completed",
                    "conclusion": "success",
                }
            ],
            "artifacts": [],
        }
        result = evaluate_devsecops_state(live)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["ci_current_head"], "PASS")
        self.assertIn(
            "CURRENT_HEAD_DEVSECOPS_ARTIFACT_MISSING",
            result["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
