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
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parents[1]
PROJECTS_FILE = REPO_ROOT / "projects" / "registry.json"
PROVIDERS_FILE = REPO_ROOT / "config" / "dev_platform" / "providers.json"
GIT_SNAPSHOT_FILE = REPO_ROOT / "docs" / "git" / "current_workspace.snapshot.json"

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
                        "version": "0.1",
                        "provider_mutations": False,
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
                project_id = unquote(path.removeprefix("/api/projects/"))
                project = project_by_id(project_id)
                if not project:
                    self._error_json(HTTPStatus.NOT_FOUND, "PROJECT_NOT_FOUND")
                    return
                self._json(
                    {
                        "project": project,
                        "branch_state": branch_state(project),
                    }
                )
                return

            self._serve_static(path)
        except (OSError, ValueError, json.JSONDecodeError):
            self._error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "CONTROL_PLANE_DATA_ERROR")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/actions/plan":
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

        self._json(plan_action(project_id, action))

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
