from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from traceability_engine import build_traceability_graph


class TraceabilityEngineTests(unittest.TestCase):
    def test_resolved_and_unresolved_evidence_are_visible(self) -> None:
        graph = build_traceability_graph(
            project={"project_id": "P-1", "name": "Project"},
            state={
                "stages": [
                    {
                        "id": "PD-01",
                        "name": "Product",
                        "gate": "PASS",
                        "status": "PASS",
                        "gate_decisions": [
                            {
                                "decision": "PASS",
                                "evidence_refs": ["EVD-1", "EVD-MISSING"],
                            }
                        ],
                        "documents": {
                            "items": [
                                {
                                    "id": "PD-002",
                                    "title": "Brief",
                                    "status": "PASS",
                                    "status_history": [
                                        {
                                            "from": "DRAFT",
                                            "to": "PASS",
                                            "evidence_refs": ["EVD-1"],
                                        }
                                    ],
                                }
                            ]
                        },
                    }
                ]
            },
            evidence=[
                {
                    "evidence_id": "EVD-1",
                    "evidence_type": "REVIEW",
                }
            ],
            events=[],
        )

        self.assertEqual(graph["integrity_status"], "PARTIAL")
        self.assertEqual(
            graph["unresolved_evidence_refs"],
            ["EVD-MISSING"],
        )
        kinds = {node["kind"] for node in graph["nodes"]}
        self.assertIn("ARTIFACT", kinds)
        self.assertIn("GATE_DECISION", kinds)
        self.assertIn("UNRESOLVED_EVIDENCE_REF", kinds)

    def test_live_provider_adds_commit_and_workflow_edges(self) -> None:
        graph = build_traceability_graph(
            project={
                "project_id": "P-1",
                "repository": "owner/repo",
                "branch": "feature/demo",
            },
            state={"stages": []},
            evidence=[],
            events=[],
            live={
                "provider": "github",
                "repository": {"full_name": "owner/repo"},
                "branch": {"name": "feature/demo", "head_sha": "abc123"},
                "workflow_runs": [
                    {
                        "id": 9,
                        "name": "CI",
                        "head_sha": "abc123",
                        "status": "completed",
                        "conclusion": "success",
                    }
                ],
                "artifacts": [
                    {
                        "id": 55,
                        "name": "father-devsecops-abc123",
                        "workflow_run_id": 9,
                    }
                ],
            },
        )
        kinds = {node["kind"] for node in graph["nodes"]}
        self.assertIn("COMMIT", kinds)
        self.assertIn("WORKFLOW_RUN", kinds)
        self.assertIn("CI_ARTIFACT", kinds)
        relations = {edge["relation"] for edge in graph["edges"]}
        self.assertIn("VALIDATES", relations)
        self.assertIn("PRODUCED", relations)


if __name__ == "__main__":
    unittest.main()
