"""Immutable local evidence and manufacturing-event store for FATHER prototype."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceStore:
    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.evidence_dir = runtime_dir / "evidence"
        self.evidence_index = runtime_dir / "evidence-index.jsonl"
        self.events_file = runtime_dir / "manufacturing-events.jsonl"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _canonical_bytes(value: Any) -> bytes:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def payload_sha256(cls, value: Any) -> str:
        return hashlib.sha256(cls._canonical_bytes(value)).hexdigest()

    @staticmethod
    def _safe_project_id(project_id: str) -> str:
        return "".join(
            char if char.isalnum() or char in "._-" else "_"
            for char in project_id
        )

    def _append_jsonl(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )

    def _iter_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    records.append(item)
        return records

    def find_by_subject_key(
        self,
        project_id: str,
        evidence_type: str,
        subject_key: str,
    ) -> dict[str, Any] | None:
        for item in reversed(self._iter_jsonl(self.evidence_index)):
            if (
                item.get("project_id") == project_id
                and item.get("evidence_type") == evidence_type
                and item.get("subject_key") == subject_key
            ):
                return item
        return None

    def store_evidence(
        self,
        *,
        project_id: str,
        evidence_type: str,
        provider: str | None,
        payload: dict[str, Any],
        subject_key: str,
        refs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self.find_by_subject_key(
            project_id,
            evidence_type,
            subject_key,
        )
        if existing:
            return {**existing, "deduplicated": True}

        evidence_id = f"EVD-{uuid.uuid4().hex[:16].upper()}"
        captured_at = self._now()
        digest = self.payload_sha256(payload)
        safe_project = self._safe_project_id(project_id)
        relative_path = (
            Path("evidence")
            / safe_project
            / f"{evidence_id}.json"
        )
        absolute_path = self.runtime_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "evidence_id": evidence_id,
            "project_id": project_id,
            "evidence_type": evidence_type,
            "provider": provider,
            "subject_key": subject_key,
            "captured_at": captured_at,
            "payload_sha256": digest,
            "refs": refs or {},
            "payload": payload,
        }

        # Exclusive creation: immutable evidence files are never overwritten.
        with absolute_path.open("x", encoding="utf-8") as handle:
            json.dump(
                record,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            handle.write("\n")

        index_record = {
            "evidence_id": evidence_id,
            "project_id": project_id,
            "evidence_type": evidence_type,
            "provider": provider,
            "subject_key": subject_key,
            "captured_at": captured_at,
            "payload_sha256": digest,
            "path": relative_path.as_posix(),
            "refs": refs or {},
        }
        self._append_jsonl(self.evidence_index, index_record)
        return {**index_record, "deduplicated": False}

    def list_evidence(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        records = [
            item
            for item in self._iter_jsonl(self.evidence_index)
            if item.get("project_id") == project_id
        ]
        return list(reversed(records[-max(1, min(limit, 200)) :]))

    def append_manufacturing_event(
        self,
        *,
        project_id: str,
        event_type: str,
        source_ref: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "event_id": f"MFG-{uuid.uuid4().hex[:16].upper()}",
            "project_id": project_id,
            "event_type": event_type,
            "source_ref": source_ref,
            "occurred_at": self._now(),
            "payload_sha256": self.payload_sha256(payload),
            "payload": payload,
        }
        self._append_jsonl(self.events_file, event)
        return event

    def list_manufacturing_events(
        self,
        project_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        records = [
            item
            for item in self._iter_jsonl(self.events_file)
            if item.get("project_id") == project_id
        ]
        return list(reversed(records[-max(1, min(limit, 500)) :]))
