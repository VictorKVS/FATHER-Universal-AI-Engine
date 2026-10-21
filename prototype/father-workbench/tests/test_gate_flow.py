from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from evidence_store import EvidenceStore
from state_store import ProjectStateStore

SERVER_FILE = APP_DIR / "server.py"
spec = importlib.util.spec_from_file_location("father_gate_flow_server", SERVER_FILE)
server = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(server)


class GateFlowIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runtime = self.root / "runtime"
        self.project = {
            "project_id": "P-1",
            "stage_state_ref": "projects/state/P-1.json",
        }
        self.state_path = self.root / "projects" / "state" / "P-1.json"
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text(
            json.dumps(
                {
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
            ),
            encoding="utf-8",
        )
        self.policy_path = self.root / "gate-policies.json"
        self.policy_path.write_text(
            json.dumps(
                {
                    "accepted_document_statuses": ["PASS", "APPROVED", "FINAL"],
                    "stages": {
                        "PD-01": {
                            "required_documents": ["PD-002", "PD-003"],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.store = ProjectStateStore(self.root)
        self.evidence = EvidenceStore(self.runtime)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_recalculate_decide_and_reject_stale_decision(self) -> None:
        with (
            patch.object(server, "project_by_id", return_value=self.project),
            patch.object(server, "PROJECT_STATE_STORE", self.store),
            patch.object(server, "EVIDENCE_STORE", self.evidence),
            patch.object(server, "GATE_POLICIES_FILE", self.policy_path),
        ):
            evaluation = server.recalculate_gate("P-1", "PD-01")
            self.assertTrue(evaluation["review_candidate"])
            self.assertEqual(evaluation["mechanical_status"], "COMPLETE")

            applied = server.decide_gate(
                "P-1",
                "PD-01",
                "PASS",
                "Reviewed required documents.",
                ["EVD-SOURCE-1"],
                "TEST-HUMAN",
                evaluation["state_etag"],
            )
            self.assertEqual(applied["status"], "APPLIED")
            self.assertTrue(applied["git_commit_required"])

            written, latest_etag = self.store.read(self.project)
            self.assertEqual(written["stages"][0]["gate"], "PASS")
            self.assertEqual(written["stages"][0]["status"], "PASS")
            self.assertEqual(applied["new_etag"], latest_etag)

            evidence = self.evidence.list_evidence("P-1")
            events = self.evidence.list_manufacturing_events("P-1")
            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["evidence_type"], "GATE_DECISION")
            self.assertEqual(events[0]["event_type"], "GATE_DECISION_APPLIED")

            stale = server.decide_gate(
                "P-1",
                "PD-01",
                "HOLD",
                "Attempt with stale state.",
                [],
                "TEST-HUMAN",
                evaluation["state_etag"],
            )
            self.assertEqual(stale["status"], "CONFLICT")
            self.assertIn("STATE_ETAG_CONFLICT", stale["errors"])


    def test_ready_stage_requires_explicit_start(self) -> None:
        state, etag = self.store.read(self.project)
        state["stages"][0]["status"] = "READY"
        ready_etag = self.store.write(self.project, state, etag)

        with (
            patch.object(server, "project_by_id", return_value=self.project),
            patch.object(server, "PROJECT_STATE_STORE", self.store),
            patch.object(server, "EVIDENCE_STORE", self.evidence),
        ):
            started = server.start_stage(
                "P-1",
                "PD-01",
                "Specialist accepted the stage.",
                "TEST-HUMAN",
                ready_etag,
            )

        self.assertEqual(started["status"], "STARTED")
        written, _ = self.store.read(self.project)
        stage = written["stages"][0]
        self.assertEqual(stage["status"], "IN_PROGRESS")
        self.assertEqual(stage["run_history"][0]["event"], "STARTED")
        events = self.evidence.list_manufacturing_events("P-1")
        self.assertEqual(events[0]["event_type"], "STAGE_STARTED")

    def test_non_ready_stage_cannot_start(self) -> None:
        _state, etag = self.store.read(self.project)
        with (
            patch.object(server, "project_by_id", return_value=self.project),
            patch.object(server, "PROJECT_STATE_STORE", self.store),
            patch.object(server, "EVIDENCE_STORE", self.evidence),
        ):
            result = server.start_stage(
                "P-1",
                "PD-01",
                "Attempt early start.",
                "TEST-HUMAN",
                etag,
            )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("STAGE_NOT_READY", result["errors"])


if __name__ == "__main__":
    unittest.main()
