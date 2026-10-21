from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from project_memory import (
    build_project_memory,
    render_project_memory_markdown,
)
from project_memory_store import (
    ProjectMemoryConflictError,
    ProjectMemoryStore,
)


class ProjectMemoryTests(unittest.TestCase):
    def project(self):
        return {
            "project_id": "P-1",
            "name": "Demo",
            "description": "Solve a verified user problem.",
            "manufactured_objects": ["Demo Service"],
        }

    def state(self):
        return {
            "project_id": "P-1",
            "description": "Demo system",
            "stages": [
                {
                    "id": "PD-01",
                    "lessons": ["Keep the vertical slice small."],
                    "decision_records": [
                        {
                            "decision_id": "DEC-1",
                            "title": "Choose adapter model",
                            "context": "Multiple providers required.",
                            "decision": "Use provider adapters.",
                            "rationale": "Avoid provider lock-in.",
                            "alternatives": ["Hard-code GitHub"],
                            "rejected_reasons": ["Creates lock-in"],
                            "constraints": ["Provider-neutral core"],
                            "evidence_refs": ["EVD-1"],
                            "owner": "Architect",
                            "status": "APPROVED",
                            "revisit_triggers": [
                                "Provider API model changes"
                            ],
                        }
                    ],
                }
            ],
        }

    def test_not_ready_project_does_not_create_draft(self):
        memory = build_project_memory(
            project=self.project(),
            state=self.state(),
            health={
                "release_ready": False,
                "overall": "IN_PROGRESS",
            },
            evidence_records=[{"evidence_id": "EVD-1"}],
            source_state_etag="state-1",
        )
        self.assertEqual(memory["status"], "NOT_READY")
        self.assertIn(
            "PROJECT_NOT_RELEASE_READY",
            memory["readiness"]["blockers"],
        )

    def test_release_ready_memory_is_source_grounded_draft(self):
        memory = build_project_memory(
            project=self.project(),
            state=self.state(),
            health={
                "release_ready": True,
                "overall": "RELEASE_READY",
            },
            evidence_records=[{"evidence_id": "EVD-1"}],
            source_state_etag="state-1",
        )
        self.assertEqual(memory["status"], "DRAFT")
        self.assertIn(
            "Avoid provider lock-in.",
            memory["sections"]["why_this_solution"],
        )
        self.assertIn(
            "EVD-1",
            memory["sections"]["key_evidence"],
        )
        markdown = render_project_memory_markdown(memory)
        self.assertIn("Why this solution", markdown)
        self.assertIn("Avoid provider lock-in.", markdown)

    def test_store_uses_optimistic_locking(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ProjectMemoryStore(Path(tmp))
            memory = build_project_memory(
                project=self.project(),
                state=self.state(),
                health={
                    "release_ready": True,
                    "overall": "RELEASE_READY",
                },
                evidence_records=[{"evidence_id": "EVD-1"}],
                source_state_etag="state-1",
            )
            etag = store.write_draft(memory, None)
            self.assertTrue(etag)
            with self.assertRaises(ProjectMemoryConflictError):
                store.write_draft(
                    {**memory, "generated_at": "changed"},
                    "stale-etag",
                )


if __name__ == "__main__":
    unittest.main()
