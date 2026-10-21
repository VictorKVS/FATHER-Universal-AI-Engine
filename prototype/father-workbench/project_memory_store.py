"""Tracked Project Memory draft persistence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from project_memory import render_project_memory_markdown


class ProjectMemoryConflictError(RuntimeError):
    """Project Memory changed after caller read it."""


class ProjectMemoryStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.root = self.repo_root / "projects" / "memory"

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
    def _safe(project_id: str) -> str:
        if not project_id:
            raise ValueError("project_id required")
        return "".join(
            c if c.isalnum() or c in "._-" else "_"
            for c in project_id
        )

    def json_path(self, project_id: str) -> Path:
        return self.root / self._safe(project_id) / "project_memory.json"

    def md_path(self, project_id: str) -> Path:
        return self.root / self._safe(project_id) / "PROJECT_MEMORY.md"

    def read(
        self,
        project_id: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        path = self.json_path(project_id)
        if not path.is_file():
            return None, None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Project Memory must be an object")
        if data.get("project_id") != project_id:
            raise ValueError("Project Memory project_id mismatch")
        return data, self.etag(data)

    @staticmethod
    def _atomic_text(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=path.parent,
            text=True,
        )
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            if temp.exists():
                temp.unlink()

    def write_draft(
        self,
        memory: dict[str, Any],
        expected_etag: str | None,
    ) -> str:
        project_id = str(memory.get("project_id") or "")
        if not project_id:
            raise ValueError("project_id required")
        if memory.get("status") != "DRAFT":
            raise ValueError("Only DRAFT Project Memory can be persisted")

        current, current_etag = self.read(project_id)
        if current and current.get("status") == "APPROVED":
            raise ValueError(
                "Approved Project Memory cannot be overwritten by DRAFT"
            )
        if current_etag != expected_etag:
            if not (current is None and expected_etag is None):
                raise ProjectMemoryConflictError(
                    "Project Memory changed"
                )

        json_content = (
            json.dumps(memory, ensure_ascii=False, indent=2) + "\n"
        )
        md_content = render_project_memory_markdown(memory)
        self._atomic_text(self.json_path(project_id), json_content)
        self._atomic_text(self.md_path(project_id), md_content)

        written, etag = self.read(project_id)
        if written != memory or not etag:
            raise OSError("Project Memory verification failed")
        return etag

    def submit_review(
        self,
        *,
        project_id: str,
        role: str,
        decision: str,
        reviewer: str,
        rationale: str,
        expected_etag: str,
    ) -> tuple[dict[str, Any], str]:
        memory, current_etag = self.read(project_id)
        if memory is None or current_etag is None:
            raise ValueError("Project Memory draft not found")
        if current_etag != expected_etag:
            raise ProjectMemoryConflictError(
                "Project Memory changed"
            )

        role = role.strip().upper()
        decision = decision.strip().upper()
        reviewer = reviewer.strip()
        rationale = rationale.strip()
        if role not in {"OWNER", "SPECIALIST"}:
            raise ValueError("INVALID_PROJECT_MEMORY_REVIEW_ROLE")
        if decision not in {"APPROVE", "HOLD", "REJECT"}:
            raise ValueError("INVALID_PROJECT_MEMORY_REVIEW_DECISION")
        if not reviewer:
            raise ValueError("PROJECT_MEMORY_REVIEWER_REQUIRED")
        if len(rationale) < 20:
            raise ValueError(
                "PROJECT_MEMORY_REVIEW_RATIONALE_TOO_SHORT"
            )
        if memory.get("status") not in {"DRAFT", "IN_REVIEW"}:
            raise ValueError("PROJECT_MEMORY_NOT_REVIEWABLE")

        reviews = list(memory.get("reviews") or [])
        reviews.append(
            {
                "role": role,
                "decision": decision,
                "reviewer": reviewer,
                "rationale": rationale,
                "reviewed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        )
        memory["reviews"] = reviews

        latest: dict[str, dict[str, Any]] = {}
        for item in reviews:
            latest[str(item.get("role") or "")] = item

        owner = latest.get("OWNER")
        specialist = latest.get("SPECIALIST")
        if (
            owner
            and specialist
            and owner.get("decision") == "APPROVE"
            and specialist.get("decision") == "APPROVE"
        ):
            memory["status"] = "APPROVED"
            memory["approved_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            memory["approved_version"] = "1"
            memory["approved_by"] = {
                "owner": owner.get("reviewer"),
                "specialist": specialist.get("reviewer"),
            }
        else:
            memory["status"] = "IN_REVIEW"

        json_content = (
            json.dumps(memory, ensure_ascii=False, indent=2)
            + "\n"
        )
        md_content = render_project_memory_markdown(memory)
        self._atomic_text(self.json_path(project_id), json_content)
        self._atomic_text(self.md_path(project_id), md_content)
        written, new_etag = self.read(project_id)
        if written != memory or not new_etag:
            raise OSError("Project Memory review verification failed")
        return memory, new_etag
