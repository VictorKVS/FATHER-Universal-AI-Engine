from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from production_records import (
    upsert_decision_record,
    upsert_risk_record,
    upsert_specialist_analysis,
)


class ProductionRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = {
            "project_id": "P-1",
            "stages": [{"id": "PD-02", "name": "Security"}],
        }

    def test_verified_analysis_requires_evidence(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "VERIFIED_ANALYSIS_REQUIRES_EVIDENCE",
        ):
            upsert_specialist_analysis(
                state=copy.deepcopy(self.state),
                stage_id="PD-02",
                analysis_id="AN-1",
                role="INFOSEC",
                title="Security analysis",
                summary="Summary",
                status="VERIFIED",
                findings=[],
                recommendations=[],
                evidence_refs=[],
                author="Tester",
            )

    def test_approved_decision_keeps_alternatives_and_revisit_trigger(self) -> None:
        result = upsert_decision_record(
            state=copy.deepcopy(self.state),
            stage_id="PD-02",
            decision_id="DEC-1",
            title="Provider choice",
            context="Need SCM provider.",
            decision="Use provider abstraction.",
            rationale="Avoid lock-in.",
            alternatives=["GitHub-only"],
            rejected_reasons=["Locks project identity to provider"],
            constraints=["Existing GitHub repository"],
            evidence_refs=["EVD-1"],
            owner="Architect",
            status="APPROVED",
            revisit_triggers=["Provider licensing changes"],
        )
        self.assertEqual(result["record"]["status"], "APPROVED")
        self.assertEqual(result["quality_warnings"], [])

    def test_accepted_risk_requires_evidence(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "RISK_TERMINAL_STATUS_REQUIRES_EVIDENCE",
        ):
            upsert_risk_record(
                state=copy.deepcopy(self.state),
                stage_id="PD-02",
                risk_id="R-1",
                title="Risk",
                description="Description",
                likelihood="MEDIUM",
                impact="HIGH",
                treatment="Accept",
                owner="Security",
                status="ACCEPTED",
                evidence_refs=[],
            )


if __name__ == "__main__":
    unittest.main()
