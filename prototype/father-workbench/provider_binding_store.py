"""Tracked Dev Platform provider bindings with optimistic locking."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BindingConflictError(RuntimeError):
    """Binding file changed since the caller read it."""


class ProviderBindingStore:
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
        return self.root / f"{self._safe_project_id(project_id)}.bindings.json"

    def default_state(self, project: dict[str, Any]) -> dict[str, Any]:
        dev = project.get("dev_platform") or {}
        return {
            "schema_version": "father.dev_platform.bindings.v0.1",
            "project_id": project["project_id"],
            "primary": {
                "provider": dev.get("primary_provider"),
                "repository": dev.get("repository") or project.get("repository"),
                "branch": dev.get("branch") or project.get("branch"),
            },
            "targets": [],
            "historical": [],
        }

    def read(
        self,
        project: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        path = self.path_for(str(project["project_id"]))
        if not path.is_file():
            state = self.default_state(project)
            return state, self.etag(state)

        with path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValueError("Provider bindings must be a JSON object")
        if state.get("project_id") != project.get("project_id"):
            raise ValueError("Provider binding project_id mismatch")
        return state, self.etag(state)

    def write(
        self,
        project: dict[str, Any],
        state: dict[str, Any],
        expected_etag: str,
    ) -> str:
        current, current_etag = self.read(project)
        del current
        if current_etag != expected_etag:
            raise BindingConflictError("Provider bindings changed")

        if state.get("project_id") != project.get("project_id"):
            raise ValueError("Provider binding project_id mismatch")

        path = self.path_for(str(project["project_id"]))
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

        written, written_etag = self.read(project)
        if written != state:
            raise OSError("Provider binding verification failed")
        return written_etag

    def switch_primary(
        self,
        project: dict[str, Any],
        *,
        target_provider: str,
        expected_etag: str,
        approval_id: str,
        verification_refs: dict[str, str],
    ) -> tuple[dict[str, Any], str, dict[str, Any]]:
        state, current_etag = self.read(project)
        if current_etag != expected_etag:
            raise BindingConflictError("Provider bindings changed")

        target_provider = target_provider.strip()
        if not target_provider:
            raise ValueError("target provider required")

        targets = list(state.get("targets") or [])
        target = next(
            (
                item
                for item in targets
                if item.get("provider") == target_provider
            ),
            None,
        )
        if not target:
            raise ValueError("target binding not configured")

        current_primary = dict(state.get("primary") or {})
        if current_primary.get("provider") == target_provider:
            raise ValueError("target provider already primary")

        switched_at = datetime.now(timezone.utc).isoformat()
        historical_entry = {
            **current_primary,
            "status": "HISTORICAL",
            "switched_out_at": switched_at,
            "switched_to": target_provider,
            "approval_id": approval_id,
            "verification_refs": dict(verification_refs),
        }
        historical = list(state.get("historical") or [])
        historical.append(historical_entry)

        state["primary"] = {
            "provider": target["provider"],
            "repository": target["repository"],
            "branch": target["branch"],
            "status": "PRIMARY",
            "switched_in_at": switched_at,
            "approval_id": approval_id,
            "verification_refs": dict(verification_refs),
        }
        remaining_targets = [
            item
            for item in targets
            if item.get("provider") != target_provider
        ]
        rollback_target = {
            "provider": current_primary.get("provider"),
            "repository": current_primary.get("repository"),
            "branch": current_primary.get("branch"),
            "status": "ROLLBACK_CANDIDATE",
            "became_rollback_candidate_at": switched_at,
            "switched_to": target_provider,
            "approval_id": approval_id,
        }
        if all(
            rollback_target.get(key)
            for key in ("provider", "repository", "branch")
        ):
            remaining_targets = [
                item
                for item in remaining_targets
                if item.get("provider") != rollback_target["provider"]
            ]
            remaining_targets.append(rollback_target)

        state["targets"] = remaining_targets
        state["historical"] = historical
        state["last_switch"] = {
            "from_provider": current_primary.get("provider"),
            "to_provider": target_provider,
            "switched_at": switched_at,
            "approval_id": approval_id,
            "verification_refs": dict(verification_refs),
        }
        state["schema_version"] = "father.dev_platform.bindings.v0.2"

        new_etag = self.write(project, state, current_etag)
        return state, new_etag, historical_entry

    def record_switch_health(
        self,
        project: dict[str, Any],
        *,
        action_id: str,
        status: str,
        blockers: list[str],
        evidence_id: str,
        rollback_recommended: bool,
        expected_etag: str,
    ) -> tuple[dict[str, Any], str]:
        state, current_etag = self.read(project)
        if current_etag != expected_etag:
            raise BindingConflictError("Provider bindings changed")

        last_switch = dict(state.get("last_switch") or {})
        if not last_switch:
            raise ValueError("last switch is not recorded")

        recorded_at = datetime.now(timezone.utc).isoformat()
        state["last_switch_health"] = {
            "action_id": action_id.strip(),
            "status": status.strip().upper(),
            "blockers": list(blockers),
            "evidence_id": evidence_id.strip(),
            "rollback_recommended": bool(rollback_recommended),
            "recorded_at": recorded_at,
            "from_provider": last_switch.get("from_provider"),
            "to_provider": last_switch.get("to_provider"),
            "switched_at": last_switch.get("switched_at"),
        }
        state["schema_version"] = "father.dev_platform.bindings.v0.3"
        new_etag = self.write(project, state, current_etag)
        return state, new_etag

    def upsert_target(
        self,
        project: dict[str, Any],
        *,
        provider: str,
        repository: str,
        branch: str,
        expected_etag: str,
    ) -> tuple[dict[str, Any], str]:
        state, current_etag = self.read(project)
        if current_etag != expected_etag:
            raise BindingConflictError("Provider bindings changed")

        target = {
            "provider": provider.strip(),
            "repository": repository.strip(),
            "branch": branch.strip(),
            "status": "CONFIGURED",
        }
        if not all(target[key] for key in ("provider", "repository", "branch")):
            raise ValueError("provider/repository/branch required")
        if target["provider"] == (state.get("primary") or {}).get("provider"):
            raise ValueError("target provider equals primary provider")

        targets = list(state.get("targets") or [])
        replaced = False
        for index, item in enumerate(targets):
            if item.get("provider") == target["provider"]:
                targets[index] = target
                replaced = True
                break
        if not replaced:
            targets.append(target)
        state["targets"] = targets
        new_etag = self.write(project, state, current_etag)
        return state, new_etag
