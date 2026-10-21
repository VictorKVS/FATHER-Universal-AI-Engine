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
