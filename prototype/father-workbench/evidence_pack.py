"""Export immutable, Git-committable FATHER project evidence packs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_evidence_pack(
    *,
    project: dict[str, Any],
    state: dict[str, Any],
    live: dict[str, Any] | None,
    devsecops: dict[str, Any],
    traceability: dict[str, Any],
    evidence_index: list[dict[str, Any]],
    manufacturing_events: list[dict[str, Any]],
) -> dict[str, Any]:
    head_sha = (
        ((live or {}).get("branch") or {}).get("head_sha")
        or "NO_HEAD"
    )
    generated_at = datetime.now(timezone.utc).isoformat()

    evidence_refs = [
        {
            "evidence_id": item.get("evidence_id"),
            "evidence_type": item.get("evidence_type"),
            "captured_at": item.get("captured_at"),
            "payload_sha256": item.get("payload_sha256"),
            "refs": item.get("refs") or {},
        }
        for item in evidence_index[:200]
    ]
    event_refs = [
        {
            "event_id": item.get("event_id"),
            "event_type": item.get("event_type"),
            "occurred_at": item.get("occurred_at"),
            "source_ref": item.get("source_ref"),
            "payload_sha256": item.get("payload_sha256"),
        }
        for item in manufacturing_events[:200]
    ]

    core = {
        "schema_version": "father.project_evidence_pack.v0.1",
        "project_id": project.get("project_id"),
        "project_name": project.get("name"),
        "generated_at": generated_at,
        "provider": (live or {}).get("provider"),
        "repository": ((live or {}).get("repository") or {}).get("full_name"),
        "branch": ((live or {}).get("branch") or {}).get("name"),
        "head_sha": head_sha,
        "project_status": project.get("status"),
        "current_stage": state.get("current_stage"),
        "stage_state_sha256": _canonical_hash(state),
        "devsecops": devsecops,
        "traceability": {
            "integrity_status": traceability.get("integrity_status"),
            "node_count": traceability.get("node_count"),
            "edge_count": traceability.get("edge_count"),
            "unresolved_evidence_refs": traceability.get(
                "unresolved_evidence_refs"
            ) or [],
        },
        "evidence_refs": evidence_refs,
        "manufacturing_event_refs": event_refs,
    }
    content_hash = _canonical_hash(core)
    pack_id = f"EVPACK-{content_hash[:20].upper()}"
    return {
        **core,
        "evidence_pack_id": pack_id,
        "content_sha256": content_hash,
    }


class EvidencePackStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def export(self, pack: dict[str, Any]) -> dict[str, Any]:
        project_id = str(pack.get("project_id") or "")
        pack_id = str(pack.get("evidence_pack_id") or "")
        if not project_id or not pack_id:
            raise ValueError("Evidence pack identity missing")

        safe_project = "".join(
            char if char.isalnum() or char in "._-" else "_"
            for char in project_id
        )
        path = (
            self.repo_root
            / "projects"
            / "evidence"
            / safe_project
            / f"{pack_id}.json"
        ).resolve()
        path.relative_to(self.repo_root)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if existing != pack:
                raise FileExistsError(
                    "Evidence pack ID collision with different content"
                )
            return {
                "evidence_pack_id": pack_id,
                "path": path.relative_to(self.repo_root).as_posix(),
                "created": False,
                "deduplicated": True,
            }

        with path.open("x", encoding="utf-8") as handle:
            json.dump(pack, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        check = json.loads(path.read_text(encoding="utf-8"))
        if check != pack:
            raise OSError("Evidence pack verification failed")

        return {
            "evidence_pack_id": pack_id,
            "path": path.relative_to(self.repo_root).as_posix(),
            "created": True,
            "deduplicated": False,
        }
