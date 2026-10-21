"""Read-only GitLab provider adapter for the FATHER control plane."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name


class GitLabAdapter:
    provider_id = "gitlab"
    write_actions = {"SCM.CREATE_BRANCH", "SCM.OPEN_CHANGE_REQUEST"}

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv("FATHER_GITLAB_TOKEN")
        configured = base_url if base_url is not None else os.getenv(
            "FATHER_GITLAB_URL",
            "https://gitlab.com",
        )
        self._base_url = configured.rstrip("/")
        self._api_url = self._base_url + "/api/v4"
        self._timeout = timeout

    @property
    def can_write(self) -> bool:
        return bool(self._token)

    @staticmethod
    def validate_branch_name(value: str) -> str:
        return validate_branch_name(value)

    @staticmethod
    def project_path(repository: str) -> str:
        value = repository.strip().strip("/")
        if "/" not in value:
            raise ValueError("GitLab repository must be namespace/project")
        return value

    def _request(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = self._api_url + path
        if query:
            url += "?" + urlencode(query)

        headers = {
            "Accept": "application/json",
            "User-Agent": "FATHER-Control-Plane/0.1",
        }
        if self._token:
            headers["PRIVATE-TOKEN"] = self._token

        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"GitLab HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitLab network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitLab returned invalid JSON") from None

    def _mutate(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
    ) -> Any:
        if not self._token:
            raise ProviderError("GitLab write credential unavailable")

        encoded_payload: dict[str, str] = {}
        for key, value in payload.items():
            if isinstance(value, bool):
                encoded_payload[key] = "true" if value else "false"
            elif value is not None:
                encoded_payload[key] = str(value)

        body = urlencode(encoded_payload).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "FATHER-Control-Plane/0.1",
            "PRIVATE-TOKEN": self._token,
        }
        request = Request(
            self._api_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(f"GitLab HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitLab network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitLab returned invalid JSON") from None

    def create_branch(
        self,
        repository: str,
        branch_name: str,
        base_ref: str,
    ) -> dict[str, Any]:
        branch_name = self.validate_branch_name(branch_name)
        base_ref = self.validate_branch_name(base_ref)
        project_path = self.project_path(repository)
        encoded_project = quote(project_path, safe="")

        created = self._mutate(
            "POST",
            f"/projects/{encoded_project}/repository/branches",
            {
                "branch": branch_name,
                "ref": base_ref,
            },
        )
        created_sha = (created.get("commit") or {}).get("id")

        reconciled = self._request(
            f"/projects/{encoded_project}/repository/branches/"
            f"{quote(branch_name, safe='')}"
        )
        reconciled_sha = (reconciled.get("commit") or {}).get("id")
        if not reconciled_sha or reconciled.get("name") != branch_name:
            raise ProviderError("GitLab branch reconciliation mismatch")
        if created_sha and created_sha != reconciled_sha:
            raise ProviderError("GitLab branch SHA reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "branch": branch_name,
            "base_ref": base_ref,
            "head_sha": reconciled_sha,
            "provider_created_sha": created_sha,
            "web_url": reconciled.get("web_url"),
            "reconciled": True,
        }

    def open_change_request(
        self,
        repository: str,
        title: str,
        head_ref: str,
        base_ref: str,
        body: str = "",
        draft: bool = True,
    ) -> dict[str, Any]:
        if not self._token:
            raise ProviderError("GitLab write credential unavailable")

        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Merge request title must be 1..200 characters")

        head_ref = self.validate_branch_name(head_ref)
        base_ref = self.validate_branch_name(base_ref)
        project_path = self.project_path(repository)
        encoded_project = quote(project_path, safe="")

        provider_title = title
        if draft and not provider_title.lower().startswith("draft:"):
            provider_title = "Draft: " + provider_title

        created = self._mutate(
            "POST",
            f"/projects/{encoded_project}/merge_requests",
            {
                "source_branch": head_ref,
                "target_branch": base_ref,
                "title": provider_title,
                "description": body[:10000],
            },
        )
        iid = created.get("iid")
        if not isinstance(iid, int):
            raise ProviderError("GitLab merge request response has no IID")

        reconciled = self._request(
            f"/projects/{encoded_project}/merge_requests/{iid}"
        )
        if (
            reconciled.get("state") != "opened"
            or reconciled.get("source_branch") != head_ref
            or reconciled.get("target_branch") != base_ref
        ):
            raise ProviderError("GitLab merge request reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "merge_request",
            "number": iid,
            "title": reconciled.get("title", provider_title),
            "state": reconciled.get("state"),
            "draft": reconciled.get("draft"),
            "head_ref": reconciled.get("source_branch"),
            "base_ref": reconciled.get("target_branch"),
            "head_sha": reconciled.get("sha"),
            "html_url": reconciled.get("web_url"),
            "reconciled": True,
        }

    @staticmethod
    def _compact_mr(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "number": value.get("iid"),
            "title": value.get("title"),
            "state": value.get("state"),
            "draft": value.get("draft"),
            "html_url": value.get("web_url"),
            "head_sha": value.get("sha"),
            "source_branch": value.get("source_branch"),
            "base_ref": value.get("target_branch"),
            "updated_at": value.get("updated_at"),
        }

    @staticmethod
    def _compact_pipeline(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": value.get("id"),
            "name": value.get("name"),
            "event": value.get("source"),
            "status": value.get("status"),
            "conclusion": value.get("status"),
            "head_sha": value.get("sha"),
            "html_url": value.get("web_url"),
            "created_at": value.get("created_at"),
            "updated_at": value.get("updated_at"),
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        project_path = self.project_path(repository)
        encoded_project = quote(project_path, safe="")
        project = self._request(f"/projects/{encoded_project}")

        default_branch = (
            project.get("default_branch")
            or default_branch_hint
            or "main"
        )
        encoded_branch = quote(branch, safe="")

        branch_data = self._request(
            f"/projects/{encoded_project}/repository/branches/{encoded_branch}"
        )
        head_sha = (branch_data.get("commit") or {}).get("id")
        if not head_sha:
            raise ProviderError("GitLab branch response has no head SHA")

        compare = self._request(
            f"/projects/{encoded_project}/repository/compare",
            {
                "from": default_branch,
                "to": branch,
            },
        )

        merge_requests = self._request(
            f"/projects/{encoded_project}/merge_requests",
            {
                "state": "opened",
                "source_branch": branch,
                "per_page": "20",
            },
        )

        pipelines = self._request(
            f"/projects/{encoded_project}/pipelines",
            {
                "ref": branch,
                "per_page": "10",
                "order_by": "updated_at",
                "sort": "desc",
            },
        )

        commits = compare.get("commits", []) if isinstance(compare, dict) else []
        compare_diffs = compare.get("diffs", []) if isinstance(compare, dict) else []
        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": project.get("path_with_namespace", repository),
                "private": project.get("visibility") == "private",
                "default_branch": default_branch,
                "archived": project.get("archived"),
                "visibility": project.get("visibility"),
                "web_url": project.get("web_url"),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": branch_data.get("protected"),
            },
            "compare": {
                "status": "diverged" if compare_diffs else "identical",
                "ahead_by": len(commits),
                "behind_by": None,
                "total_commits": len(commits),
            },
            "change_requests": [
                self._compact_mr(item)
                for item in merge_requests
            ] if isinstance(merge_requests, list) else [],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_pipeline(item)
                for item in pipelines
            ] if isinstance(pipelines, list) else [],
        }
