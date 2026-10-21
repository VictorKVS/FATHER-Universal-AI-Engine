from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from state_store import ProjectStateStore, StateConflictError


class ProjectStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.project = {
            "project_id": "P-1",
            "stage_state_ref": "projects/state.json",
        }
        path = self.root / "projects" / "state.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "project_id": "P-1",
                    "stages": [{"id": "PD-01", "gate": "NOT_READY"}],
                }
            ),
            encoding="utf-8",
        )
        self.store = ProjectStateStore(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_atomic_write_requires_current_etag(self) -> None:
        state, etag = self.store.read(self.project)
        state["stages"][0]["gate"] = "PASS"
        new_etag = self.store.write(self.project, state, etag)

        written, check_etag = self.store.read(self.project)
        self.assertEqual(written["stages"][0]["gate"], "PASS")
        self.assertEqual(new_etag, check_etag)

    def test_stale_etag_is_rejected(self) -> None:
        state, etag = self.store.read(self.project)
        first = dict(state)
        first["note"] = "first"
        self.store.write(self.project, first, etag)

        state["note"] = "stale"
        with self.assertRaises(StateConflictError):
            self.store.write(self.project, state, etag)

    def test_path_cannot_escape_repository(self) -> None:
        bad_project = {
            "project_id": "P-1",
            "stage_state_ref": "../outside.json",
        }
        with self.assertRaises(ValueError):
            self.store.path_for_project(bad_project)


if __name__ == "__main__":
    unittest.main()
