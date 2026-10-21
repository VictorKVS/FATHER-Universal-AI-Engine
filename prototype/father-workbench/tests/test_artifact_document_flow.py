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

from document_store import DocumentStore
from evidence_store import EvidenceStore
from state_store import ProjectStateStore

SERVER_FILE = APP_DIR / "server.py"
spec = importlib.util.spec_from_file_location("father_artifact_flow_server", SERVER_FILE)
server = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(server)


class ArtifactDocumentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = {
            "project_id": "P-1",
            "stage_state_ref": "projects/state/P-1.json",
        }
        state_path = self.root / "projects" / "state" / "P-1.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(
            json.dumps(
                {
                    "project_id": "P-1",
                    "stages": [
                        {
                            "id": "PD-01",
                            "name": "Product",
                            "status": "IN_PROGRESS",
                            "gate": "NOT_READY",
                            "documents": {
                                "done": 0,
                                "total": 1,
                                "items": [
                                    {
                                        "id": "PD-002",
                                        "title": "Product Brief",
                                        "status": "DRAFT",
                                        "source_ref": "docs/PD-002.md",
                                    }
                                ],
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        policy = self.root / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "accepted_document_statuses": ["PASS"],
                    "stages": {
                        "PD-01": {
                            "required_documents": ["PD-002"],
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.policy_path = policy
        self.state_store = ProjectStateStore(self.root)
        self.document_store = DocumentStore(self.root)
        self.evidence_store = EvidenceStore(self.root / "runtime")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def patches(self):
        return (
            patch.object(server, "project_by_id", return_value=self.project),
            patch.object(server, "PROJECT_STATE_STORE", self.state_store),
            patch.object(server, "DOCUMENT_STORE", self.document_store),
            patch.object(server, "EVIDENCE_STORE", self.evidence_store),
            patch.object(server, "GATE_POLICIES_FILE", self.policy_path),
        )

    def test_document_write_records_hash_evidence(self) -> None:
        with self.patches()[0], self.patches()[1], self.patches()[2], self.patches()[3]:
            result = server.write_artifact_document(
                "P-1",
                "PD-01",
                "PD-002",
                "# Product Brief\n",
                "NEW",
                "Initial document.",
                "TEST",
            )

        self.assertEqual(result["status"], "UPDATED")
        self.assertTrue(result["git_commit_required"])
        self.assertNotEqual(
            result["document"]["new_sha256"],
            "NEW",
        )
        evidence = self.evidence_store.list_evidence("P-1")
        self.assertEqual(
            evidence[0]["evidence_type"],
            "DOCUMENT_CONTENT_CHANGE",
        )

    def test_artifact_pass_then_gate_becomes_review_candidate(self) -> None:
        state, etag = self.state_store.read(self.project)
        self.assertEqual(state["stages"][0]["documents"]["done"], 0)

        with (
            patch.object(server, "project_by_id", return_value=self.project),
            patch.object(server, "PROJECT_STATE_STORE", self.state_store),
            patch.object(server, "EVIDENCE_STORE", self.evidence_store),
            patch.object(server, "GATE_POLICIES_FILE", self.policy_path),
        ):
            result = server.update_artifact(
                "P-1",
                "PD-01",
                "PD-002",
                "Product Brief",
                "PASS",
                "Reviewed.",
                ["EVD-SOURCE"],
                "TEST",
                etag,
                "docs/PD-002.md",
            )

        self.assertEqual(result["status"], "APPLIED")
        self.assertTrue(
            result["gate_evaluation"]["review_candidate"]
        )
        self.assertFalse(
            result["gate_evaluation"]["can_auto_pass"]
        )


if __name__ == "__main__":
    unittest.main()
