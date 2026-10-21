"""Atomic project state persistence with optimistic locking."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from gate_engine import state_etag


class StateConflictError(RuntimeError):
    """The tracked state changed after the caller read it."""


class ProjectStateStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def path_for_project(self, project: dict[str, Any]) -> Path:
        reference = project.get("stage_state_ref")
        if not reference:
            raise FileNotFoundError("Project has no stage_state_ref")
        path = (self.repo_root / str(reference)).resolve()
        path.relative_to(self.repo_root)
        return path

    def read(self, project: dict[str, Any]) -> tuple[dict[str, Any], str]:
        path = self.path_for_project(project)
        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValueError("Project state must be a JSON object")
        if state.get("project_id") != project.get("project_id"):
            raise ValueError("Stage state project_id mismatch")
        return state, state_etag(state)

    def write(
        self,
        project: dict[str, Any],
        state: dict[str, Any],
        expected_etag: str,
    ) -> str:
        path = self.path_for_project(project)
        current, current_etag = self.read(project)
        del current
        if current_etag != expected_etag:
            raise StateConflictError(
                "Project state changed; refresh before applying decision"
            )

        if state.get("project_id") != project.get("project_id"):
            raise ValueError("Updated state project_id mismatch")

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
                    sort_keys=False,
                    indent=2,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

        written, written_etag = self.read(project)
        if written != state:
            raise OSError("Project state verification failed after atomic write")
        return written_etag
