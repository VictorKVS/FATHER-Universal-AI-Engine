"""Read-only GitVerse provider adapter for the FATHER control plane."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError


class GitVerseAdapter:
    provider_id = "gitverse"

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv("FATHER_GITVERSE_TOKEN")
        self._base_url = (
            base_url if base_url is not None else os.getenv(
                "FATHER_GITVERSE_URL",
                "https://api.gitverse.ru",
            )
        ).rstrip("/")
        self._timeout = timeout

    @staticmethod
    def split_repository(repository: str) -> tuple[str, str]:
        parts = [part for part in repository.strip().split("/") if part]
        if len(parts) != 2:
            raise ValueError("GitVerse repository must be owner/name")
        return parts[0], parts[1]

    def _request(self, path: str, query: dict[str, str] | None = None) -> Any:
        url = self._base_url + path
        if query:
            url += "?" + urlencode(query)

        headers = {
            "Accept": "application/vnd.gitverse.object+json;version=latest",
            "User-Agent": "FATHER-Control-Plane/0.1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"GitVerse HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitVerse network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitVerse returned invalid JSON") from None

    @staticmethod
    def _head_sha(branch_data: dict[str, Any]) -> str | None:
        commit = branch_data.get("commit") or {}
        return commit.get("sha") or commit.get("id")

    @staticmethod
    def _compact_pull(value: dict[str, Any]) -> dict[str, Any]:
        head = value.get("head") or {}
        base = value.get("base") or {}
        return {
            "number": value.get("number"),
            "title": value.get("title"),
            "state": value.get("state"),
            "draft": value.get("draft"),
            "html_url": value.get("html_url"),
            "head_sha": head.get("sha"),
            "source_branch": head.get("ref") or head.get("label"),
            "base_ref": base.get("ref") or base.get("label"),
            "updated_at": value.get("updated_at"),
        }

    @staticmethod
    def _compact_run(value: dict[str, Any]) -> dict[str, Any]:
        status = value.get("status")
        conclusion = value.get("conclusion")
        if conclusion is None and status in {
            "success",
            "failure",
            "cancelled",
            "skipped",
        }:
            conclusion = status
            status = "completed"
        return {
            "id": value.get("id"),
            "name": value.get("name") or value.get("title"),
            "event": value.get("event"),
            "status": status,
            "conclusion": conclusion,
            "head_sha": value.get("head_sha") or value.get("commit_sha"),
            "html_url": value.get("html_url"),
            "created_at": value.get("created_at") or value.get("started"),
            "updated_at": value.get("updated_at") or value.get("stopped"),
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        owner, name = self.split_repository(repository)
        repo_path = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        repo = self._request(repo_path)
        default_branch = (
            repo.get("default_branch")
            or default_branch_hint
            or "main"
        )

        branch_data = self._request(
            f"{repo_path}/branches/{quote(branch, safe='')}"
        )
        head_sha = self._head_sha(branch_data)
        if not head_sha:
            raise ProviderError("GitVerse branch response has no head SHA")

        compare = self._request(
            f"{repo_path}/compare/"
            f"{quote(default_branch, safe='')}...{quote(branch, safe='')}"
        )
        pulls = self._request(
            f"{repo_path}/pulls",
            {"per_page": "30"},
        )
        runs = self._request(
            f"{repo_path}/actions/runs",
            {"branch": branch, "per_page": "10"},
        )

        pull_items = pulls if isinstance(pulls, list) else pulls.get("pulls", [])
        pull_items = [
            item for item in pull_items
            if (item.get("state") in {None, "open"})
            and (
                ((item.get("head") or {}).get("ref") == branch)
                or ((item.get("head") or {}).get("label") == branch)
            )
        ]

        run_items = []
        if isinstance(runs, list):
            run_items = runs
        elif isinstance(runs, dict):
            run_items = (
                runs.get("workflow_runs")
                or runs.get("runs")
                or runs.get("actions")
                or []
            )

        commits = compare.get("commits", []) if isinstance(compare, dict) else []
        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": repo.get("full_name", repository),
                "private": repo.get("private"),
                "default_branch": default_branch,
                "archived": repo.get("archived"),
                "visibility": repo.get("visibility"),
                "web_url": repo.get("html_url"),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": branch_data.get("protected"),
            },
            "compare": {
                "status": compare.get("status") if isinstance(compare, dict) else None,
                "ahead_by": compare.get("ahead_by") if isinstance(compare, dict) else None,
                "behind_by": compare.get("behind_by") if isinstance(compare, dict) else None,
                "total_commits": (
                    compare.get("total_commits", len(commits))
                    if isinstance(compare, dict)
                    else None
                ),
            },
            "change_requests": [
                self._compact_pull(item) for item in pull_items
            ],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_run(item) for item in run_items
            ],
        }
