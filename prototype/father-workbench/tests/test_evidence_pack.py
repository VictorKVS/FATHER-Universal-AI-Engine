from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evidence_pack import EvidencePackStore, build_evidence_pack


class EvidencePackTests(unittest.TestCase):
    def test_build_and_export_is_content_addressed(self) -> None:
        pack = build_evidence_pack(
            project={"project_id": "P-1", "name": "Demo", "status": "DEV"},
            state={"project_id": "P-1", "current_stage": "DEV", "stages": []},
            live={
                "provider": "github",
                "repository": {"full_name": "owner/repo"},
                "branch": {"name": "feature/demo", "head_sha": "abc123"},
            },
            devsecops={"status": "PASS", "head_sha": "abc123"},
            traceability={
                "integrity_status": "PASS",
                "node_count": 1,
                "edge_count": 0,
                "unresolved_evidence_refs": [],
            },
            evidence_index=[],
            manufacturing_events=[],
        )
        self.assertTrue(pack["evidence_pack_id"].startswith("EVPACK-"))
        self.assertEqual(pack["head_sha"], "abc123")
        self.assertEqual(pack["pack_status"], "COMPLETE")

        with tempfile.TemporaryDirectory() as tmp:
            store = EvidencePackStore(Path(tmp))
            first = store.export(pack)
            second = store.export(pack)
            self.assertTrue(first["created"])
            self.assertTrue(second["deduplicated"])
            self.assertEqual(first["path"], second["path"])
            listed = store.list("P-1")
            self.assertEqual(len(listed), 1)
            self.assertEqual(
                listed[0]["evidence_pack_id"],
                pack["evidence_pack_id"],
            )


if __name__ == "__main__":
    unittest.main()
