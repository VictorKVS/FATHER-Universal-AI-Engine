#!/usr/bin/env python3
"""FATHER Project Workbench prototype control-plane server.

Zero external dependencies. Serves the UI and a policy-gated control API.
Provider credentials remain server-side; supported mutations are explicit,
audited and reconciled.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from evidence_store import EvidenceStore
from gate_engine import (
    apply_gate_decision,
    evaluate_stage_gate,
    validate_gate_decision,
)
from lifecycle_engine import reconcile_project_flow
from migration_engine import build_migration_plan
from state_store import ProjectStateStore, StateConflictError
from providers.base import ProviderError
from providers.github_adapter import GitHubAdapter
from providers.gitlab_adapter import GitLabAdapter
from providers.gitverse_adapter import GitVerseAdapter
from providers.sourcecraft_adapter import SourceCraftAdapter
from providers.gitflic_adapter import GitFlicAdapter

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
PROJECTS_FILE = REPO_ROOT / "projects" / "registry.json"
PROVIDERS_FILE = REPO_ROOT / "config" / "dev_platform" / "providers.json"
GIT_SNAPSHOT_FILE = REPO_ROOT / "docs" / "git" / "current_workspace.snapshot.json"
GATE_POLICIES_FILE = REPO_ROOT / "config" / "gates" / "stage_gate_policies.json"
STAGE_FLOW_FILE = REPO_ROOT / "config" / "lifecycle" / "project_stage_flow.json"
RUNTIME_DIR = APP_DIR / "runtime"
AUDIT_FILE = RUNTIME_DIR / "scm-actions.jsonl"
EVIDENCE_STORE = EvidenceStore(RUNTIME_DIR)
PROJECT_STATE_STORE = ProjectStateStore(REPO_ROOT)

MAX_JSON_BODY = 16 * 1024

SAFE_ACTIONS = {
    "SCM.CREATE_BRANCH",
    "SCM.OPEN_CHANGE_REQUEST",
    "SCM.REQUEST_REVIEW",
    "SCM.ADD_LABEL",
    "SCM.ADD_COMMENT",
    "SCM.CREATE_WORK_ITEM",
    "SCM.UPDATE_WORK_ITEM",
    "SCM.TRIGGER_PIPELINE",
    "SCM.RETRY_JOB",
    "SCM.CREATE_RELEASE_DRAFT",
    "PROVIDER.ADD_MIRROR",
    "PROVIDER.MIGRATE_REPOSITORY",
    "PROVIDER.VERIFY_MIGRATION",
}
HIGH_IMPACT_ACTIONS = {
    "SCM.MERGE_CHANGE_REQUEST",
    "SCM.DELETE_BRANCH",
    "SCM.PUBLISH_RELEASE",
    "PROVIDER.SWITCH_PRIMARY",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path}")
    return value


def project_by_id(project_id: str) -> dict[str, Any] | None:
    data = read_json(PROJECTS_FILE)
    for project in data.get("projects", []):
        if project.get("project_id") == project_id:
            return project
    return None


def provider_config_by_id(provider_id: str) -> dict[str, Any] | None:
    data = read_json(PROVIDERS_FILE)
    for provider in data.get("providers", []):
        if provider.get("id") == provider_id:
            return provider
    return None


def provider_supports_action(provider_id: str, action: str) -> bool:
    provider = provider_config_by_id(provider_id)
    if not provider:
        return False
    return action in set(provider.get("write_capabilities") or [])


def provider_runtime_catalog() -> dict[str, Any]:
    registry = read_json(PROVIDERS_FILE)
    runtime: list[dict[str, Any]] = []
    for provider in registry.get("providers", []):
        provider_id = str(provider.get("id") or "")
        try:
            adapter = provider_adapter(provider_id)
            adapter_loaded = True
            credential_configured = bool(
                getattr(adapter, "_token", None)
            )
        except NotImplementedError:
            adapter_loaded = False
            credential_configured = False

        runtime.append(
            {
                "id": provider_id,
                "adapter_status": provider.get("adapter_status"),
                "adapter_loaded": adapter_loaded,
                "credential_configured": credential_configured,
                "write_capabilities": provider.get("write_capabilities") or [],
                "draft_change_request_supported": provider.get(
                    "draft_change_request_supported"
                ),
                "branch_create_status": provider.get("branch_create_status"),
                "write_discovery_status": provider.get("write_discovery_status"),
            }
        )

    return {
        "schema_version": "father.dev_platform.runtime.v0.1",
        "providers": runtime,
    }


def provider_write_capabilities() -> dict[str, list[str]]:
    registry = read_json(PROVIDERS_FILE)
    return {
        str(provider.get("id")): list(provider.get("write_capabilities") or [])
        for provider in registry.get("providers", [])
        if provider.get("write_capabilities")
    }


def branch_state(project: dict[str, Any]) -> dict[str, Any] | None:
    snapshot = read_json(GIT_SNAPSHOT_FILE)
    branch_name = project.get("branch")
    for branch in snapshot.get("branches", []):
        if branch.get("branch") == branch_name:
            return branch
    return None


def project_stage_state(project: dict[str, Any]) -> dict[str, Any]:
    state, _etag = PROJECT_STATE_STORE.read(project)
    return state


def stage_by_id(project: dict[str, Any], stage_id: str) -> dict[str, Any] | None:
    state = project_stage_state(project)
    for stage in state.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    return None


def provider_adapter(provider: str):
    if provider == "github":
        return GitHubAdapter()
    if provider == "gitlab":
        return GitLabAdapter()
    if provider == "gitverse":
        return GitVerseAdapter()
    if provider == "sourcecraft":
        return SourceCraftAdapter()
    if provider == "gitflic":
        return GitFlicAdapter()
    raise NotImplementedError(f"Provider adapter not implemented: {provider}")


def live_provider_state(project: dict[str, Any]) -> dict[str, Any]:
    dev_platform = project.get("dev_platform") or {}
    provider = str(dev_platform.get("primary_provider") or "")
    repository = dev_platform.get("repository") or project.get("repository")
    branch = dev_platform.get("branch") or project.get("branch")
    if not repository or not branch:
        raise ValueError("Project has no repository/branch binding")

    adapter = provider_adapter(provider)
    return adapter.live_state(str(repository), str(branch))


def provider_state_subject_key(
    project: dict[str, Any],
    live: dict[str, Any],
) -> str:
    repository = (live.get("repository") or {}).get("full_name") or project.get("repository")
    branch = (live.get("branch") or {}).get("name") or project.get("branch")
    head_sha = (live.get("branch") or {}).get("head_sha") or "NO_HEAD"
    workflow = (live.get("workflow_runs") or [{}])[0] if live.get("workflow_runs") else {}
    workflow_key = ":".join(
        str(value or "-")
        for value in (
            workflow.get("id"),
            workflow.get("status"),
            workflow.get("conclusion"),
        )
    )
    change_requests = ",".join(
        f"{item.get('number')}:{item.get('state')}:{item.get('updated_at')}"
        for item in live.get("change_requests", [])
    )
    return "|".join(
        [
            str(live.get("provider") or "unknown"),
            str(repository or "unknown"),
            str(branch or "unknown"),
            str(head_sha),
            workflow_key,
            change_requests,
        ]
    )


def capture_live_provider_evidence(
    project: dict[str, Any],
    live: dict[str, Any],
    source_ref: str = "LIVE_READ",
) -> dict[str, Any]:
    evidence = EVIDENCE_STORE.store_evidence(
        project_id=str(project["project_id"]),
        evidence_type="PROVIDER_STATE",
        provider=str(live.get("provider") or ""),
        payload=live,
        subject_key=provider_state_subject_key(project, live),
        refs={"source_ref": source_ref},
    )
    if not evidence.get("deduplicated"):
        EVIDENCE_STORE.append_manufacturing_event(
            project_id=str(project["project_id"]),
            event_type="PROVIDER_STATE_OBSERVED",
            source_ref=evidence["evidence_id"],
            payload={
                "provider": live.get("provider"),
                "repository": (live.get("repository") or {}).get("full_name"),
                "branch": (live.get("branch") or {}).get("name"),
                "head_sha": (live.get("branch") or {}).get("head_sha"),
                "evidence_id": evidence["evidence_id"],
            },
        )
    return evidence


def recalculate_gate(
    project_id: str,
    stage_id: str,
) -> dict[str, Any]:
    project = project_by_id(project_id)
    if not project:
        return {
            "valid": False,
            "errors": ["PROJECT_NOT_FOUND"],
        }
    state, _etag = PROJECT_STATE_STORE.read(project)
    return evaluate_stage_gate(
        state,
        stage_id,
        read_json(GATE_POLICIES_FILE),
    )


def decide_gate(
    project_id: str,
    stage_id: str,
    decision: str,
    rationale: str,
    evidence_refs: list[str],
    decided_by: str,
    expected_etag: str,
) -> dict[str, Any]:
    project = project_by_id(project_id)
    if not project:
        return {
            "status": "BLOCKED",
            "errors": ["PROJECT_NOT_FOUND"],
        }

    state, current_etag = PROJECT_STATE_STORE.read(project)
    if current_etag != expected_etag:
        return {
            "status": "CONFLICT",
            "errors": ["STATE_ETAG_CONFLICT"],
            "current_etag": current_etag,
        }

    policies = read_json(GATE_POLICIES_FILE)
    validation = validate_gate_decision(
        state,
        stage_id,
        decision,
        rationale,
        evidence_refs,
        policies,
    )
    if not validation["valid"]:
        return {
            "status": "BLOCKED",
            "errors": validation["errors"],
            "evaluation": validation["evaluation"],
            "current_etag": current_etag,
        }

    updated = apply_gate_decision(
        state,
        stage_id,
        decision,
        rationale,
        evidence_refs,
        decided_by,
        policies,
    )
    lifecycle = reconcile_project_flow(
        updated,
        read_json(STAGE_FLOW_FILE),
    )
    updated = lifecycle["state"]

    try:
        new_etag = PROJECT_STATE_STORE.write(
            project,
            updated,
            current_etag,
        )
    except StateConflictError:
        _state, latest_etag = PROJECT_STATE_STORE.read(project)
        return {
            "status": "CONFLICT",
            "errors": ["STATE_ETAG_CONFLICT"],
            "current_etag": latest_etag,
        }

    payload = {
        "project_id": project_id,
        "stage_id": stage_id,
        "decision": decision.upper().strip(),
        "rationale": rationale.strip(),
        "evidence_refs": evidence_refs,
        "decided_by": decided_by.strip() or "HUMAN",
        "previous_etag": current_etag,
        "new_etag": new_etag,
        "lifecycle": {
            "previous_current_stage": lifecycle["previous_current_stage"],
            "current_stage": lifecycle["current_stage"],
            "changes": lifecycle["changes"],
        },
    }
    event = EVIDENCE_STORE.append_manufacturing_event(
        project_id=project_id,
        event_type="GATE_DECISION_APPLIED",
        source_ref=f"GATE:{stage_id}:{new_etag[:12]}",
        payload=payload,
    )
    evidence = EVIDENCE_STORE.store_evidence(
        project_id=project_id,
        evidence_type="GATE_DECISION",
        provider=None,
        payload=payload,
        subject_key=f"{stage_id}:{new_etag}",
        refs={
            "manufacturing_event_id": event["event_id"],
            "input_evidence_refs": evidence_refs,
        },
    )
    return {
        "status": "APPLIED",
        "project_id": project_id,
        "stage_id": stage_id,
        "decision": decision.upper().strip(),
        "previous_etag": current_etag,
        "new_etag": new_etag,
        "evidence": evidence,
        "manufacturing_event_id": event["event_id"],
        "lifecycle": payload["lifecycle"],
        "worktree_change": True,
        "git_commit_required": True,
    }


def write_audit_event(event: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def execute_action(
    project_id: str,
    action: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    plan = plan_action(project_id, action)
    action_id = plan["action_id"]

    if not plan.get("allowed"):
        return plan

    if action not in {"SCM.CREATE_BRANCH", "SCM.OPEN_CHANGE_REQUEST"}:
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["ACTION_EXECUTION_NOT_IMPLEMENTED"],
        }

    project = project_by_id(project_id)
    if not project:
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["PROJECT_NOT_FOUND"],
        }

    dev_platform = project.get("dev_platform") or {}
    provider = str(dev_platform.get("primary_provider") or "")
    try:
        adapter = provider_adapter(provider)
    except NotImplementedError:
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["PROVIDER_WRITE_ADAPTER_NOT_IMPLEMENTED"],
        }

    if not provider_supports_action(provider, action):
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["PROVIDER_ACTION_NOT_SUPPORTED"],
        }
    if not adapter.can_write:
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["PROVIDER_WRITE_CREDENTIAL_UNAVAILABLE"],
        }

    repository = str(
        dev_platform.get("repository")
        or project.get("repository")
        or ""
    ).strip()
    if not repository:
        return {
            **plan,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["REPOSITORY_BINDING_REQUIRED"],
        }

    if action == "SCM.CREATE_BRANCH":
        branch_name = str(params.get("branch_name", "")).strip()
        base_ref = str(
            params.get("base_ref")
            or dev_platform.get("branch")
            or project.get("branch")
            or ""
        ).strip()
        if not branch_name or not base_ref:
            return {
                **plan,
                "status": "BLOCKED",
                "allowed": False,
                "reasons": ["BRANCH_NAME_AND_BASE_REQUIRED"],
            }
        target = {
            "repository": repository,
            "branch_name": branch_name,
            "base_ref": base_ref,
        }
    else:
        title = str(params.get("title", "")).strip()
        head_ref = str(
            params.get("head_ref")
            or dev_platform.get("branch")
            or project.get("branch")
            or ""
        ).strip()
        base_ref = str(params.get("base_ref", "")).strip()
        body = str(params.get("body", ""))
        draft = bool(params.get("draft", True))
        if not title or not head_ref or not base_ref:
            return {
                **plan,
                "status": "BLOCKED",
                "allowed": False,
                "reasons": ["TITLE_HEAD_AND_BASE_REQUIRED"],
            }
        target = {
            "repository": repository,
            "title": title,
            "head_ref": head_ref,
            "base_ref": base_ref,
            "draft": draft,
        }

    started = {
        "action_id": action_id,
        "project_id": project_id,
        "provider": provider,
        "action": action,
        "status": "EXECUTING",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
    }
    write_audit_event(started)
    EVIDENCE_STORE.append_manufacturing_event(
        project_id=project_id,
        event_type="ACTION_STARTED",
        source_ref=action_id,
        payload=started,
    )

    try:
        if action == "SCM.CREATE_BRANCH":
            result = adapter.create_branch(
                repository,
                branch_name,
                base_ref,
            )
        else:
            result = adapter.open_change_request(
                repository,
                title,
                head_ref,
                base_ref,
                body=body,
                draft=draft,
            )
    except (ProviderError, ValueError) as exc:
        failed = {
            **started,
            "status": "FAILED",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
        write_audit_event(failed)
        EVIDENCE_STORE.append_manufacturing_event(
            project_id=project_id,
            event_type="ACTION_FAILED",
            source_ref=action_id,
            payload=failed,
        )
        return {
            "action_id": action_id,
            "project_id": project_id,
            "action": action,
            "status": "FAILED",
            "allowed": False,
            "reasons": ["PROVIDER_MUTATION_FAILED"],
            "provider_mutation": False,
        }

    succeeded = {
        **started,
        "status": "SUCCEEDED",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    write_audit_event(succeeded)

    event = EVIDENCE_STORE.append_manufacturing_event(
        project_id=project_id,
        event_type="ACTION_SUCCEEDED",
        source_ref=action_id,
        payload=succeeded,
    )
    try:
        evidence = EVIDENCE_STORE.store_evidence(
            project_id=project_id,
            evidence_type="SCM_ACTION_RESULT",
            provider=str(provider or ""),
            payload=result,
            subject_key=action_id,
            refs={
                "action_id": action_id,
                "manufacturing_event_id": event["event_id"],
            },
        )
    except OSError:
        degraded = {
            **succeeded,
            "status": "SUCCEEDED_EVIDENCE_DEGRADED",
            "evidence_error": "EVIDENCE_PERSIST_FAILED",
        }
        write_audit_event(degraded)
        EVIDENCE_STORE.append_manufacturing_event(
            project_id=project_id,
            event_type="EVIDENCE_PERSIST_FAILED",
            source_ref=action_id,
            payload={
                "action_id": action_id,
                "provider_mutation": True,
            },
        )
        return {
            "action_id": action_id,
            "project_id": project_id,
            "action": action,
            "status": "SUCCEEDED_EVIDENCE_DEGRADED",
            "allowed": False,
            "reasons": ["EVIDENCE_PERSIST_FAILED"],
            "provider_mutation": True,
            "result": result,
        }

    return {
        "action_id": action_id,
        "project_id": project_id,
        "action": action,
        "status": "SUCCEEDED",
        "allowed": True,
        "reasons": [],
        "provider_mutation": True,
        "result": result,
        "evidence": evidence,
        "manufacturing_event_id": event["event_id"],
    }


def plan_action(project_id: str, action: str) -> dict[str, Any]:
    project = project_by_id(project_id)
    action_id = f"ACT-{uuid.uuid4().hex[:12].upper()}"

    if not project:
        return {
            "action_id": action_id,
            "project_id": project_id,
            "action": action,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["PROJECT_NOT_FOUND"],
            "provider_mutation": False,
        }

    if action not in SAFE_ACTIONS | HIGH_IMPACT_ACTIONS:
        return {
            "action_id": action_id,
            "project_id": project_id,
            "action": action,
            "status": "BLOCKED",
            "allowed": False,
            "reasons": ["ACTION_NOT_ALLOWLISTED"],
            "provider_mutation": False,
        }

    reasons: list[str] = []
    branch = branch_state(project)

    if action == "SCM.MERGE_CHANGE_REQUEST":
        if project.get("security_gate") != "PASS":
            reasons.append("SECURITY_GATE_NOT_PASS")
        if not branch:
            reasons.append("BRANCH_EVIDENCE_UNAVAILABLE")
        elif branch.get("relation_to_main") in {"DIVERGED", "BEHIND"}:
            reasons.append(f"BRANCH_{branch.get('relation_to_main')}")
        reasons.append("EXPLICIT_MERGE_APPROVAL_REQUIRED")

    if action == "PROVIDER.SWITCH_PRIMARY":
        reasons.extend(
            [
                "MIGRATION_VERIFICATION_EVIDENCE_REQUIRED",
                "EXPLICIT_PROVIDER_SWITCH_APPROVAL_REQUIRED",
            ]
        )

    if action == "SCM.PUBLISH_RELEASE":
        reasons.append("EXPLICIT_RELEASE_APPROVAL_REQUIRED")

    if action == "SCM.DELETE_BRANCH":
        reasons.append("EXPLICIT_DELETE_APPROVAL_REQUIRED")

    dev_platform = project.get("dev_platform") or {}
    provider = str(dev_platform.get("primary_provider") or "")
    executable_actions = {"SCM.CREATE_BRANCH", "SCM.OPEN_CHANGE_REQUEST"}

    if action in executable_actions:
        if not provider_config_by_id(provider):
            reasons.append("PROVIDER_NOT_REGISTERED")
        elif not provider_supports_action(provider, action):
            reasons.append("PROVIDER_ACTION_NOT_SUPPORTED")
        else:
            try:
                provider_adapter(provider)
            except NotImplementedError:
                reasons.append("PROVIDER_ADAPTER_NOT_IMPLEMENTED")
    elif action in SAFE_ACTIONS:
        reasons.append("ACTION_EXECUTION_NOT_IMPLEMENTED")

    allowed = not reasons and action in SAFE_ACTIONS
    return {
        "action_id": action_id,
        "project_id": project_id,
        "action": action,
        "status": "READY" if allowed else "BLOCKED",
        "allowed": allowed,
        "reasons": reasons,
        "provider_mutation": False,
        "note": "Prototype plan only. External provider mutation is disabled.",
    }


class FatherHandler(BaseHTTPRequestHandler):
    server_version = "FATHERWorkbench/0.1"

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'",
        )

    def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _error_json(self, status: int, code: str) -> None:
        self._json({"error": code, "status": status}, status)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path

        try:
            if path == "/api/health":
                self._json(
                    {
                        "status": "ok",
                        "service": "father-project-workbench",
                        "version": "0.2",
                        "provider_mutations": provider_write_capabilities(),
                        "stage_state_api": True,
                        "live_provider_read": [
                            "github",
                            "gitlab",
                            "gitverse",
                            "sourcecraft",
                            "gitflic",
                        ],
                        "evidence_store": True,
                        "manufacturing_events": True,
                        "gate_engine": True,
                        "atomic_project_state": True,
                    }
                )
                return

            if path == "/api/projects":
                self._json(read_json(PROJECTS_FILE))
                return

            if path == "/api/providers":
                self._json(read_json(PROVIDERS_FILE))
                return

            if path == "/api/providers/runtime":
                self._json(provider_runtime_catalog())
                return

            if path == "/api/git-snapshot":
                self._json(read_json(GIT_SNAPSHOT_FILE))
                return

            if path.startswith("/api/projects/"):
                parts = [unquote(part) for part in path.split("/") if part]
                if len(parts) < 3:
                    self._error_json(HTTPStatus.NOT_FOUND, "ENDPOINT_NOT_FOUND")
                    return

                project_id = parts[2]
                project = project_by_id(project_id)
                if not project:
                    self._error_json(HTTPStatus.NOT_FOUND, "PROJECT_NOT_FOUND")
                    return

                if len(parts) == 3:
                    self._json(
                        {
                            "project": project,
                            "branch_state": branch_state(project),
                            "stage_state": project_stage_state(project),
                        }
                    )
                    return

                if len(parts) == 4 and parts[3] == "evidence":
                    self._json(
                        {
                            "project_id": project_id,
                            "evidence": EVIDENCE_STORE.list_evidence(project_id),
                        }
                    )
                    return

                if (
                    len(parts) == 4
                    and parts[3] == "manufacturing-events"
                ):
                    self._json(
                        {
                            "project_id": project_id,
                            "events": EVIDENCE_STORE.list_manufacturing_events(
                                project_id
                            ),
                        }
                    )
                    return

                if len(parts) == 4 and parts[3] == "stages":
                    self._json(project_stage_state(project))
                    return

                if len(parts) == 5 and parts[3] == "stages":
                    stage = stage_by_id(project, parts[4])
                    if not stage:
                        self._error_json(HTTPStatus.NOT_FOUND, "STAGE_NOT_FOUND")
                        return
                    self._json(
                        {
                            "project_id": project_id,
                            "stage": stage,
                        }
                    )
                    return

                if (
                    len(parts) == 5
                    and parts[3] == "dev-platform"
                    and parts[4] == "live"
                ):
                    try:
                        live = live_provider_state(project)
                        try:
                            evidence = capture_live_provider_evidence(project, live)
                            evidence_status = "CAPTURED"
                        except OSError:
                            evidence = None
                            evidence_status = "PERSIST_FAILED"
                        self._json(
                            {
                                "project_id": project_id,
                                "live": live,
                                "evidence": evidence,
                                "evidence_status": evidence_status,
                            }
                        )
                    except NotImplementedError:
                        self._error_json(
                            HTTPStatus.NOT_IMPLEMENTED,
                            "PROVIDER_ADAPTER_NOT_IMPLEMENTED",
                        )
                    except ProviderError:
                        self._error_json(
                            HTTPStatus.BAD_GATEWAY,
                            "PROVIDER_READ_FAILED",
                        )
                    return

                self._error_json(HTTPStatus.NOT_FOUND, "ENDPOINT_NOT_FOUND")
                return

            self._serve_static(path)
        except (OSError, ValueError, json.JSONDecodeError):
            self._error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "CONTROL_PLANE_DATA_ERROR")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {
            "/api/actions/plan",
            "/api/actions/execute",
            "/api/migrations/plan",
            "/api/gates/recalculate",
            "/api/gates/decide",
        }:
            self._error_json(HTTPStatus.NOT_FOUND, "ENDPOINT_NOT_FOUND")
            return

        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            self._error_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "JSON_REQUIRED")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error_json(HTTPStatus.BAD_REQUEST, "INVALID_CONTENT_LENGTH")
            return

        if length <= 0 or length > MAX_JSON_BODY:
            self._error_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "INVALID_BODY_SIZE")
            return

        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error_json(HTTPStatus.BAD_REQUEST, "INVALID_JSON")
            return

        project_id = str(body.get("project_id", "")).strip()
        if not project_id:
            self._error_json(HTTPStatus.BAD_REQUEST, "PROJECT_REQUIRED")
            return

        if path == "/api/gates/recalculate":
            stage_id = str(body.get("stage_id", "")).strip()
            if not stage_id:
                self._error_json(HTTPStatus.BAD_REQUEST, "STAGE_REQUIRED")
                return
            result = recalculate_gate(project_id, stage_id)
            status = (
                HTTPStatus.NOT_FOUND
                if "PROJECT_NOT_FOUND" in result.get("errors", [])
                else HTTPStatus.OK
            )
            self._json(result, status)
            return

        if path == "/api/gates/decide":
            if self.headers.get("X-FATHER-Action") != "confirm":
                self._error_json(
                    HTTPStatus.FORBIDDEN,
                    "EXPLICIT_ACTION_HEADER_REQUIRED",
                )
                return
            if body.get("confirm") is not True:
                self._error_json(
                    HTTPStatus.FORBIDDEN,
                    "EXPLICIT_CONFIRMATION_REQUIRED",
                )
                return

            stage_id = str(body.get("stage_id", "")).strip()
            decision = str(body.get("decision", "")).strip()
            rationale = str(body.get("rationale", "")).strip()
            expected_etag = str(body.get("expected_etag", "")).strip()
            decided_by = str(body.get("decided_by", "HUMAN")).strip()
            evidence_refs = body.get("evidence_refs") or []

            if (
                not stage_id
                or not decision
                or not expected_etag
                or not isinstance(evidence_refs, list)
            ):
                self._error_json(
                    HTTPStatus.BAD_REQUEST,
                    "INVALID_GATE_DECISION_REQUEST",
                )
                return
            evidence_refs = [
                str(item).strip()
                for item in evidence_refs[:50]
                if str(item).strip()
            ]

            result = decide_gate(
                project_id,
                stage_id,
                decision,
                rationale,
                evidence_refs,
                decided_by,
                expected_etag,
            )
            if result["status"] == "CONFLICT":
                self._json(result, HTTPStatus.CONFLICT)
            elif result["status"] == "BLOCKED":
                self._json(result, HTTPStatus.BAD_REQUEST)
            else:
                self._json(result)
            return

        if path == "/api/migrations/plan":
            target_provider = str(body.get("target_provider", "")).strip()
            if not target_provider:
                self._error_json(
                    HTTPStatus.BAD_REQUEST,
                    "TARGET_PROVIDER_REQUIRED",
                )
                return
            project = project_by_id(project_id)
            if not project:
                self._error_json(HTTPStatus.NOT_FOUND, "PROJECT_NOT_FOUND")
                return
            plan = build_migration_plan(
                project,
                target_provider,
                read_json(PROVIDERS_FILE),
            )
            EVIDENCE_STORE.append_manufacturing_event(
                project_id=project_id,
                event_type="MIGRATION_PLAN_CREATED",
                source_ref=plan["plan_id"],
                payload={
                    "source_provider": plan["source_provider"],
                    "target_provider": plan["target_provider"],
                    "state": plan["state"],
                    "blockers": plan["blockers"],
                },
            )
            self._json(plan)
            return

        action = str(body.get("action", "")).strip()
        if not action:
            self._error_json(HTTPStatus.BAD_REQUEST, "ACTION_REQUIRED")
            return

        if path == "/api/actions/plan":
            self._json(plan_action(project_id, action))
            return

        if self.headers.get("X-FATHER-Action") != "confirm":
            self._error_json(HTTPStatus.FORBIDDEN, "EXPLICIT_ACTION_HEADER_REQUIRED")
            return
        if body.get("confirm") is not True:
            self._error_json(HTTPStatus.FORBIDDEN, "EXPLICIT_CONFIRMATION_REQUIRED")
            return

        params = body.get("params") or {}
        if not isinstance(params, dict):
            self._error_json(HTTPStatus.BAD_REQUEST, "PARAMS_MUST_BE_OBJECT")
            return

        self._json(execute_action(project_id, action, params))

    def _serve_static(self, request_path: str) -> None:
        relative = request_path.lstrip("/") or "index.html"
        if relative.startswith("prototype/father-workbench/"):
            relative = relative.removeprefix("prototype/father-workbench/")

        candidate = (APP_DIR / unquote(relative)).resolve()
        try:
            candidate.relative_to(APP_DIR)
        except ValueError:
            self._error_json(HTTPStatus.FORBIDDEN, "PATH_OUTSIDE_APP")
            return

        if candidate.is_dir():
            candidate = candidate / "index.html"

        if not candidate.is_file():
            self._error_json(HTTPStatus.NOT_FOUND, "FILE_NOT_FOUND")
            return

        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or candidate.suffix in {".js", ".json"}:
            content_type += "; charset=utf-8"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[FATHER] {self.address_string()} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FATHER Project Workbench prototype")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8094)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), FatherHandler)
    print(f"FATHER Project Workbench: http://{args.host}:{args.port}/")
    print("External provider mutations: LIMITED / POLICY-GATED")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
