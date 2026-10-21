"""Read-only GitHub provider adapter for the FATHER control plane."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

GITHUB_API = "https://api.github.com"


class ProviderError(RuntimeError):
    """Provider request failed without exposing credentials."""


class GitHubAdapter:
    provider_id = "github"

    def __init__(self, token: str | None = None, timeout: float = 8.0) -> None:
        self._token = token if token is not None else os.getenv("FATHER_GITHUB_TOKEN")
        self._timeout = timeout

    @staticmethod
    def split_repository(repository: str) -> tuple[str, str]:
        parts = [part for part in repository.strip().split("/") if part]
        if len(parts) != 2:
            raise ValueError("GitHub repository must be owner/name")
        return parts[0], parts[1]

    def _request(self, path: str, query: dict[str, str] | None = None) -> Any:
        url = GITHUB_API + path
        if query:
            url += "?" + urlencode(query)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "FATHER-Control-Plane/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"GitHub HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitHub network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitHub returned invalid JSON") from None

    @staticmethod
    def _compact_user(value: dict[str, Any] | None) -> dict[str, Any] | None:
        if not value:
            return None
        return {
            "login": value.get("login"),
            "type": value.get("type"),
        }

    @staticmethod
    def _compact_pull(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "number": value.get("number"),
            "title": value.get("title"),
            "state": value.get("state"),
            "draft": value.get("draft"),
            "html_url": value.get("html_url"),
            "head_sha": (value.get("head") or {}).get("sha"),
            "base_ref": (value.get("base") or {}).get("ref"),
            "user": GitHubAdapter._compact_user(value.get("user")),
            "updated_at": value.get("updated_at"),
        }

    @staticmethod
    def _compact_check(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": value.get("id"),
            "name": value.get("name"),
            "status": value.get("status"),
            "conclusion": value.get("conclusion"),
            "details_url": value.get("details_url"),
            "started_at": value.get("started_at"),
            "completed_at": value.get("completed_at"),
        }

    @staticmethod
    def _compact_workflow(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": value.get("id"),
            "name": value.get("name"),
            "event": value.get("event"),
            "status": value.get("status"),
            "conclusion": value.get("conclusion"),
            "head_sha": value.get("head_sha"),
            "html_url": value.get("html_url"),
            "created_at": value.get("created_at"),
            "updated_at": value.get("updated_at"),
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        owner, name = self.split_repository(repository)
        repo_path = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        repository_data = self._request(repo_path)

        default_branch = (
            repository_data.get("default_branch")
            or default_branch_hint
            or "main"
        )
        encoded_branch = quote(branch, safe="")
        encoded_default = quote(default_branch, safe="")

        branch_data = self._request(f"{repo_path}/branches/{encoded_branch}")
        head_sha = (branch_data.get("commit") or {}).get("sha")
        if not head_sha:
            raise ProviderError("GitHub branch response has no head SHA")

        compare_data = self._request(
            f"{repo_path}/compare/{encoded_default}...{encoded_branch}"
        )
        pulls_data = self._request(
            f"{repo_path}/pulls",
            {
                "state": "open",
                "head": f"{owner}:{branch}",
                "per_page": "20",
            },
        )
        checks_data = self._request(
            f"{repo_path}/commits/{quote(head_sha, safe='')}/check-runs",
            {"per_page": "100"},
        )
        combined_status = self._request(
            f"{repo_path}/commits/{quote(head_sha, safe='')}/status"
        )
        workflow_data = self._request(
            f"{repo_path}/actions/runs",
            {"branch": branch, "per_page": "10"},
        )

        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": repository_data.get("full_name", repository),
                "private": repository_data.get("private"),
                "default_branch": default_branch,
                "archived": repository_data.get("archived"),
                "visibility": repository_data.get("visibility"),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": branch_data.get("protected"),
            },
            "compare": {
                "status": compare_data.get("status"),
                "ahead_by": compare_data.get("ahead_by"),
                "behind_by": compare_data.get("behind_by"),
                "total_commits": compare_data.get("total_commits"),
            },
            "change_requests": [
                self._compact_pull(item) for item in pulls_data
            ] if isinstance(pulls_data, list) else [],
            "checks": [
                self._compact_check(item)
                for item in checks_data.get("check_runs", [])
            ] if isinstance(checks_data, dict) else [],
            "combined_status": {
                "state": combined_status.get("state"),
                "total_count": combined_status.get("total_count"),
                "statuses": [
                    {
                        "context": item.get("context"),
                        "state": item.get("state"),
                        "description": item.get("description"),
                        "target_url": item.get("target_url"),
                    }
                    for item in combined_status.get("statuses", [])
                ],
            } if isinstance(combined_status, dict) else None,
            "workflow_runs": [
                self._compact_workflow(item)
                for item in workflow_data.get("workflow_runs", [])
            ] if isinstance(workflow_data, dict) else [],
        }
