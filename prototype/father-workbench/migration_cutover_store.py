"""Tracked cutover approvals for FATHER Dev Platform migrations."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CutoverConflictError(RuntimeError):
    """Tracked cutover approval state changed."""


class MigrationCutoverStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.root = self.repo_root / "projects" / "dev_platform"

    @staticmethod
    def etag(value: dict[str, Any]) -> str:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _safe_project_id(project_id: str) -> str:
        if not project_id:
            raise ValueError("project_id required")
        return "".join(
            char if char.isalnum() or char in "._-" else "_"
            for char in project_id
        )

    def path_for(self, project_id: str) -> Path:
        return self.root / (
            f"{self._safe_project_id(project_id)}.cutover-approvals.json"
        )

    def default_state(self, project_id: str) -> dict[str, Any]:
        return {
            "schema_version": "father.migration_cutover_approvals.v0.1",
            "project_id": project_id,
            "approvals": [],
        }

    def read(self, project_id: str) -> tuple[dict[str, Any], str]:
        path = self.path_for(project_id)
        if not path.is_file():
            state = self.default_state(project_id)
            return state, self.etag(state)
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValueError("Cutover approval state must be an object")
        if state.get("project_id") != project_id:
            raise ValueError("Cutover approval project_id mismatch")
        return state, self.etag(state)

    def write(
        self,
        project_id: str,
        state: dict[str, Any],
        expected_etag: str,
    ) -> str:
        current, current_etag = self.read(project_id)
        del current
        if current_etag != expected_etag:
            raise CutoverConflictError("Cutover approval state changed")
        if state.get("project_id") != project_id:
            raise ValueError("Cutover approval project_id mismatch")

        path = self.path_for(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=path.parent,
            text=True,
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    state,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

        written, etag = self.read(project_id)
        if written != state:
            raise OSError("Cutover approval verification failed")
        return etag

    def append(
        self,
        *,
        project_id: str,
        target_provider: str,
        decision: str,
        rationale: str,
        approved_by: str,
        security_review_id: str,
        verification_refs: dict[str, str],
        expected_etag: str,
    ) -> tuple[dict[str, Any], str]:
        decision = decision.strip().upper()
        if decision not in {"APPROVE", "HOLD", "CANCEL"}:
            raise ValueError("Invalid cutover decision")
        rationale = rationale.strip()
        approved_by = approved_by.strip()
        if len(rationale) < 20:
            raise ValueError("Cutover rationale too short")
        if not approved_by:
            raise ValueError("Cutover approver required")
        if decision == "APPROVE" and not security_review_id:
            raise ValueError("Approved security review required")

        state, current_etag = self.read(project_id)
        if current_etag != expected_etag:
            raise CutoverConflictError("Cutover approval state changed")

        material = {
            "project_id": project_id,
            "target_provider": target_provider,
            "decision": decision,
            "rationale": rationale,
            "approved_by": approved_by,
            "security_review_id": security_review_id,
            "verification_refs": verification_refs,
        }
        digest = hashlib.sha256(
            json.dumps(
                material,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        approval = {
            "approval_id": f"CUTOVER-{digest[:16].upper()}",
            **material,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "record_sha256": digest,
        }
        state.setdefault("approvals", []).append(approval)
        new_etag = self.write(project_id, state, current_etag)
        return approval, new_etag

    def latest_for_target(
        self,
        project_id: str,
        target_provider: str,
    ) -> dict[str, Any] | None:
        state, _etag = self.read(project_id)
        for approval in reversed(state.get("approvals", [])):
            if approval.get("target_provider") == target_provider:
                return approval
        return None
