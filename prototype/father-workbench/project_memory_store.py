"""Tracked Project Memory draft persistence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
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
