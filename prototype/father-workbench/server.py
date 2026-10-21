#!/usr/bin/env python3
"""FATHER Project Workbench prototype control-plane server.

Zero external dependencies. Serves the UI and a small read/policy API.
It never stores provider credentials and never mutates an external SCM provider.
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
RUNTIME_DIR = APP_DIR / "runtime"
AUDIT_FILE = RUNTIME_DIR / "scm-actions.jsonl"
EVIDENCE_STORE = EvidenceStore(RUNTIME_DIR)

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


def branch_state(project: dict[str, Any]) -> dict[str, Any] | None:
    snapshot = read_json(GIT_SNAPSHOT_FILE)
    branch_name = project.get("branch")
    for branch in snapshot.get("branches", []):
        if branch.get("branch") == branch_name:
            return branch
    return None


def project_stage_state(project: dict[str, Any]) -> dict[str, Any]:
    reference = project.get("stage_state_ref")
    if not reference:
        raise FileNotFoundError("Project has no stage_state_ref")
    path = (REPO_ROOT / str(reference)).resolve()
    path.relative_to(REPO_ROOT)
    state = read_json(path)
    if state.get("project_id") != project.get("project_id"):
        raise ValueError("Stage state project_id mismatch")
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

    write_actions = getattr(adapter, "write_actions", set())
    if action not in write_actions:
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
        try:
            adapter = provider_adapter(provider)
            if action not in getattr(adapter, "write_actions", set()):
                reasons.append("PROVIDER_ACTION_NOT_SUPPORTED")
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
                        "provider_mutations": {
                            "github": [
                                "SCM.CREATE_BRANCH",
                                "SCM.OPEN_CHANGE_REQUEST",
                            ],
                            "gitlab": [
                                "SCM.CREATE_BRANCH",
                                "SCM.OPEN_CHANGE_REQUEST",
                            ],
                        },
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
                    }
                )
                return

            if path == "/api/projects":
                self._json(read_json(PROJECTS_FILE))
                return

            if path == "/api/providers":
                self._json(read_json(PROVIDERS_FILE))
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
        if path not in {"/api/actions/plan", "/api/actions/execute"}:
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
        action = str(body.get("action", "")).strip()
        if not project_id or not action:
            self._error_json(HTTPStatus.BAD_REQUEST, "PROJECT_AND_ACTION_REQUIRED")
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
    print("External provider mutations: DISABLED")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
