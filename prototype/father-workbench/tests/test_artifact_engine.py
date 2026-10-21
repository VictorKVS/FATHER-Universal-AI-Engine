from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from artifact_engine import apply_artifact_update, list_artifacts, validate_artifact_update


class ArtifactEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = {
            "project_id": "P-1",
            "stages": [
                {
                    "id": "PD-01",
                    "name": "Product",
                    "documents": {
                        "done": 0,
                        "total": 2,
                        "items": [
                            {
                                "id": "PD-002",
                                "title": "Product Brief",
                                "status": "DRAFT",
                            }
                        ],
                    },
                }
            ],
        }

    def test_pass_requires_evidence(self) -> None:
        result = validate_artifact_update(
            state=self.state,
            stage_id="PD-01",
            artifact_id="PD-002",
            title="Product Brief",
            status="PASS",
            rationale="Reviewed",
            evidence_refs=[],
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "EVIDENCE_REFS_REQUIRED_FOR_PASS",
            result["errors"],
        )

    def test_existing_artifact_status_is_versioned(self) -> None:
        state = copy.deepcopy(self.state)
        result = apply_artifact_update(
            state=state,
            stage_id="PD-01",
            artifact_id="PD-002",
            title="Product Brief",
            status="PASS",
            rationale="Reviewed against evidence.",
            evidence_refs=["EVD-1"],
            decided_by="TEST",
        )
        artifact = result["artifact"]
        self.assertEqual(artifact["status"], "PASS")
        self.assertEqual(
            artifact["status_history"][0]["from"],
            "DRAFT",
        )
        self.assertEqual(result["accepted_count"], 1)

    def test_missing_artifact_can_be_created_as_draft(self) -> None:
        state = copy.deepcopy(self.state)
        result = apply_artifact_update(
            state=state,
            stage_id="PD-01",
            artifact_id="PD-003",
            title="Stakeholder Map",
            status="DRAFT",
            rationale="Initial artifact registration.",
            evidence_refs=[],
            decided_by="TEST",
            source_ref="docs/PD-003.md",
        )
        self.assertEqual(result["artifact"]["id"], "PD-003")
        self.assertEqual(
            result["artifact"]["source_ref"],
            "docs/PD-003.md",
        )

    def test_list_artifacts_preserves_stage_context(self) -> None:
        artifacts = list_artifacts(self.state)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["stage_id"], "PD-01")


if __name__ == "__main__":
    unittest.main()
