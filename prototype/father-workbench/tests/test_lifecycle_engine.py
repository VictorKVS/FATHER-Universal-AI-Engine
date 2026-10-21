from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from lifecycle_engine import reconcile_project_flow


class LifecycleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = {
            "stages": [
                {"id": "PD-01", "requires": []},
                {"id": "PD-02", "requires": ["PD-01"]},
                {"id": "DS-02", "requires": ["PD-01"]},
                {"id": "PD-03", "requires": ["PD-02", "DS-02"]},
            ]
        }
        self.state = {
            "current_stage": "PD-01",
            "stages": [
                {"id": "PD-01", "status": "PASS", "gate": "PASS"},
                {"id": "PD-02", "status": "IN_PROGRESS", "gate": "NOT_READY"},
                {"id": "DS-02", "status": "WAITING", "gate": "WAITING"},
                {"id": "PD-03", "status": "BLOCKED", "gate": "BLOCKED"},
            ],
        }

    def test_parallel_security_stages_become_eligible_after_product(self) -> None:
        result = reconcile_project_flow(
            copy.deepcopy(self.state),
            self.flow,
        )
        self.assertTrue(result["eligibility"]["PD-02"])
        self.assertTrue(result["eligibility"]["DS-02"])
        self.assertFalse(result["eligibility"]["PD-03"])
        self.assertEqual(result["current_stage"], "PD-02")

        ds = next(
            item
            for item in result["state"]["stages"]
            if item["id"] == "DS-02"
        )
        self.assertEqual(ds["status"], "READY")

    def test_compliance_waits_for_both_security_gates(self) -> None:
        state = copy.deepcopy(self.state)
        next(item for item in state["stages"] if item["id"] == "PD-02").update(
            {"gate": "PASS", "status": "PASS"}
        )
        result = reconcile_project_flow(state, self.flow)
        self.assertEqual(result["current_stage"], "DS-02")
        self.assertFalse(result["eligibility"]["PD-03"])

        next(item for item in state["stages"] if item["id"] == "DS-02").update(
            {"gate": "PASS", "status": "PASS"}
        )
        result = reconcile_project_flow(state, self.flow)
        self.assertTrue(result["eligibility"]["PD-03"])
        self.assertEqual(result["current_stage"], "PD-03")
        compliance = next(
            item
            for item in result["state"]["stages"]
            if item["id"] == "PD-03"
        )
        self.assertEqual(compliance["status"], "READY")

    def test_ready_does_not_become_in_progress_automatically(self) -> None:
        state = copy.deepcopy(self.state)
        state["stages"][1]["status"] = "BLOCKED"
        result = reconcile_project_flow(state, self.flow)
        self.assertEqual(result["state"]["stages"][1]["status"], "READY")


if __name__ == "__main__":
    unittest.main()
