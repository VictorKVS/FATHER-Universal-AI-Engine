from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from evidence_store import EvidenceStore


class EvidenceStoreTests(unittest.TestCase):
    def test_evidence_is_immutable_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp))
            first = store.store_evidence(
                project_id="P-1",
                evidence_type="PROVIDER_STATE",
                provider="github",
                payload={"head_sha": "abc"},
                subject_key="github:repo:branch:abc",
            )
            second = store.store_evidence(
                project_id="P-1",
                evidence_type="PROVIDER_STATE",
                provider="github",
                payload={"head_sha": "abc"},
                subject_key="github:repo:branch:abc",
            )

            self.assertFalse(first["deduplicated"])
            self.assertTrue(second["deduplicated"])
            self.assertEqual(first["evidence_id"], second["evidence_id"])
            self.assertEqual(len(store.list_evidence("P-1")), 1)

            evidence_path = Path(tmp) / first["path"]
            self.assertTrue(evidence_path.is_file())

    def test_manufacturing_events_are_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp))
            one = store.append_manufacturing_event(
                project_id="P-1",
                event_type="ACTION_STARTED",
                source_ref="ACT-1",
                payload={"status": "EXECUTING"},
            )
            two = store.append_manufacturing_event(
                project_id="P-1",
                event_type="ACTION_SUCCEEDED",
                source_ref="ACT-1",
                payload={"status": "SUCCEEDED"},
            )
            events = store.list_manufacturing_events("P-1")
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["event_id"], two["event_id"])
            self.assertEqual(events[1]["event_id"], one["event_id"])

    def test_payload_hash_is_stable_for_key_order(self) -> None:
        left = EvidenceStore.payload_sha256({"a": 1, "b": 2})
        right = EvidenceStore.payload_sha256({"b": 2, "a": 1})
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
