from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from gate_engine import (
    apply_gate_decision,
    evaluate_stage_gate,
    validate_gate_decision,
)


class GateEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policies = {
            "accepted_document_statuses": ["PASS", "APPROVED", "FINAL"],
            "stages": {
                "PD-01": {
                    "required_documents": ["PD-002", "PD-003"],
                }
            },
        }
        self.state = {
            "project_id": "P-1",
            "stages": [
                {
                    "id": "PD-01",
                    "status": "IN_PROGRESS",
                    "gate": "NOT_READY",
                    "documents": {
                        "items": [
                            {"id": "PD-002", "status": "PASS"},
                            {"id": "PD-003", "status": "PASS"},
                        ]
                    },
                }
            ],
        }

    def test_complete_stage_is_review_candidate_not_auto_pass(self) -> None:
        result = evaluate_stage_gate(
            self.state,
            "PD-01",
            self.policies,
        )
        self.assertTrue(result["review_candidate"])
        self.assertFalse(result["can_auto_pass"])
        self.assertEqual(
            result["recommended_action"],
            "READY_FOR_HUMAN_REVIEW",
        )

    def test_missing_document_blocks_mechanical_completion(self) -> None:
        state = copy.deepcopy(self.state)
        state["stages"][0]["documents"]["items"].pop()
        result = evaluate_stage_gate(state, "PD-01", self.policies)
        self.assertFalse(result["review_candidate"])
        self.assertIn("PD-003", result["missing_documents"])

    def test_pass_requires_evidence_and_rationale(self) -> None:
        result = validate_gate_decision(
            self.state,
            "PD-01",
            "PASS",
            "",
            [],
            self.policies,
        )
        self.assertFalse(result["valid"])
        self.assertIn("RATIONALE_REQUIRED", result["errors"])
        self.assertIn("EVIDENCE_REFS_REQUIRED", result["errors"])

    def test_human_pass_records_decision(self) -> None:
        state = copy.deepcopy(self.state)
        updated = apply_gate_decision(
            state,
            "PD-01",
            "PASS",
            "Required documents reviewed.",
            ["EVD-1"],
            "HUMAN",
            self.policies,
        )
        stage = updated["stages"][0]
        self.assertEqual(stage["gate"], "PASS")
        self.assertEqual(stage["status"], "PASS")
        self.assertEqual(stage["gate_decisions"][0]["evidence_refs"], ["EVD-1"])

    def test_no_policy_cannot_pass(self) -> None:
        result = validate_gate_decision(
            self.state,
            "PD-99",
            "PASS",
            "test",
            ["EVD-1"],
            self.policies,
        )
        self.assertFalse(result["valid"])
        self.assertIn("GATE_POLICY_NOT_DEFINED", result["errors"])


if __name__ == "__main__":
    unittest.main()
