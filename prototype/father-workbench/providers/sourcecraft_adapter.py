"""SourceCraft provider adapter for the FATHER control plane.

Public REST API currently gives FATHER:
- repository metadata;
- branch inventory;
- pull requests;
- CI/CD runs;
- pull-request creation.

A documented REST branch-create endpoint was not confirmed during this implementation,
so SCM.CREATE_BRANCH is intentionally not implemented for SourceCraft.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name


class SourceCraftAdapter:
    provider_id = "sourcecraft"
    write_actions = {"SCM.OPEN_CHANGE_REQUEST"}

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv(
            "FATHER_SOURCECRAFT_TOKEN"
        )
        self._base_url = (
            base_url if base_url is not None else os.getenv(
                "FATHER_SOURCECRAFT_URL",
                "https://api.sourcecraft.tech",
            )
        ).rstrip("/")
        self._timeout = timeout

    @property
    def can_write(self) -> bool:
        return bool(self._token)

    @staticmethod
    def split_repository(repository: str) -> tuple[str, str]:
        parts = [part for part in repository.strip().split("/") if part]
        if len(parts) != 2:
            raise ValueError("SourceCraft repository must be org/repo")
        return parts[0], parts[1]

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FATHER-Control-Plane/0.1",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _request(self, path: str, query: dict[str, str] | None = None) -> Any:
        url = self._base_url + path
        if query:
            url += "?" + urlencode(query)
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"SourceCraft HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"SourceCraft network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("SourceCraft returned invalid JSON") from None

    def _mutate(self, method: str, path: str, payload: dict[str, Any]) -> Any:
        if not self._token:
            raise ProviderError("SourceCraft write credential unavailable")
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self._base_url + path,
            data=body,
            headers=self._headers("application/json"),
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(f"SourceCraft HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"SourceCraft network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("SourceCraft returned invalid JSON") from None

    @staticmethod
    def _branch_sha(value: dict[str, Any]) -> str | None:
        return (value.get("commit") or {}).get("hash")

    @staticmethod
    def _compact_pull(value: dict[str, Any]) -> dict[str, Any]:
        source = value.get("source") or {}
        target = value.get("target") or {}
        return {
            "number": value.get("slug") or value.get("id"),
            "title": value.get("title"),
            "state": value.get("status"),
            "draft": value.get("status") == "draft",
            "html_url": value.get("web_url"),
            "head_sha": source.get("sha"),
            "source_branch": value.get("source_branch") or source.get("ref"),
            "base_ref": value.get("target_branch") or target.get("ref"),
            "updated_at": value.get("updated_at"),
        }

    @staticmethod
    def _compact_run(value: dict[str, Any]) -> dict[str, Any]:
        dates = value.get("dates") or {}
        status = value.get("status")
        conclusion = None
        if status in {"success", "failure", "cancelled", "skipped"}:
            conclusion = status
            status = "completed"
        return {
            "id": value.get("id"),
            "name": value.get("name") or value.get("slug"),
            "event": value.get("trigger") or value.get("event"),
            "status": status,
            "conclusion": conclusion,
            "head_sha": value.get("commit_hash") or value.get("sha"),
            "html_url": value.get("web_url"),
            "created_at": dates.get("created_at") or value.get("created_at"),
            "updated_at": dates.get("updated_at") or value.get("updated_at"),
        }

    def ref_inventory(self, repository: str) -> dict[str, Any]:
        org, repo_name = self.split_repository(repository)
        root = f"/repos/{quote(org, safe='')}/{quote(repo_name, safe='')}"
        repo = self._request(root)
        branches: dict[str, str] = {}
        limitations = ["TAG_INVENTORY_API_NOT_VERIFIED"]

        for page in range(1, 101):
            data = self._request(
                f"{root}/branches",
                {
                    "page_size": "100",
                    "page": str(page),
                },
            )
            items = data.get("branches", []) if isinstance(data, dict) else []
            for item in items:
                sha = self._branch_sha(item)
                if item.get("name") and sha:
                    branches[str(item["name"])] = str(sha)
            next_page = data.get("next_page") if isinstance(data, dict) else None
            if len(items) < 100 and not next_page:
                break
        else:
            limitations.append("BRANCH_PAGINATION_LIMIT_REACHED")

        return {
            "provider": self.provider_id,
            "repository": (
                f"{(repo.get('organization') or {}).get('slug', org)}/"
                f"{repo.get('slug', repo_name)}"
            ),
            "default_branch": repo.get("default_branch"),
            "branches": branches,
            "tags": {},
            "complete": False,
            "limitations": limitations,
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        org, repo_name = self.split_repository(repository)
        repo_path = f"/repos/{quote(org, safe='')}/{quote(repo_name, safe='')}"
        repo = self._request(repo_path)
        default_branch = (
            repo.get("default_branch")
            or default_branch_hint
            or "main"
        )

        branch_list = self._request(
            f"{repo_path}/branches",
            {
                "filter": branch,
                "page_size": "100",
            },
        )
        branches = branch_list.get("branches", []) if isinstance(branch_list, dict) else []
        branch_data = next(
            (item for item in branches if item.get("name") == branch),
            None,
        )
        if not branch_data:
            raise ProviderError("SourceCraft branch not found")
        head_sha = self._branch_sha(branch_data)
        if not head_sha:
            raise ProviderError("SourceCraft branch response has no head hash")

        pull_data = self._request(
            f"{repo_path}/pulls",
            {
                "filter": f'source_branch="{branch}"',
                "page_size": "50",
            },
        )
        pulls = pull_data.get("pull_requests", []) if isinstance(pull_data, dict) else []
        pulls = [
            item
            for item in pulls
            if item.get("status") in {"draft", "open", "merging"}
        ]

        run_data = self._request(
            f"{repo_path}/cicd/runs",
            {"page_size": "10"},
        )
        runs = run_data.get("runs", []) if isinstance(run_data, dict) else []
        runs = [
            item
            for item in runs
            if (
                not item.get("branch")
                or item.get("branch") == branch
                or item.get("ref") == branch
            )
        ][:10]

        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": (
                    f"{(repo.get('organization') or {}).get('slug', org)}/"
                    f"{repo.get('slug', repo_name)}"
                ),
                "private": repo.get("visibility") == "private",
                "default_branch": default_branch,
                "archived": repo.get("archived"),
                "visibility": repo.get("visibility"),
                "web_url": repo.get("web_url"),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": branch_data.get("protected"),
            },
            "compare": {
                "status": "UNKNOWN",
                "ahead_by": None,
                "behind_by": None,
                "total_commits": None,
                "note": "No verified branch-compare REST endpoint wired in this adapter.",
            },
            "change_requests": [
                self._compact_pull(item) for item in pulls
            ],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_run(item) for item in runs
            ],
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
            raise ProviderError("SourceCraft write credential unavailable")

        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Pull request title must be 1..200 characters")
        head_ref = validate_branch_name(head_ref)
        base_ref = validate_branch_name(base_ref)
        org, repo_name = self.split_repository(repository)
        repo_path = f"/repos/{quote(org, safe='')}/{quote(repo_name, safe='')}"

        created = self._mutate(
            "POST",
            f"{repo_path}/pulls",
            {
                "title": title,
                "description": body[:10000],
                "source_branch": head_ref,
                "target_branch": base_ref,
                "reviewer_ids": [],
                "publish": not draft,
            },
        )
        slug = created.get("slug")
        if not slug:
            raise ProviderError("SourceCraft pull request response has no slug")

        reconciled = self._request(
            f"{repo_path}/pulls/{quote(str(slug), safe='')}"
        )
        actual_source = (
            reconciled.get("source_branch")
            or (reconciled.get("source") or {}).get("ref")
        )
        actual_target = (
            reconciled.get("target_branch")
            or (reconciled.get("target") or {}).get("ref")
        )
        expected_states = {"draft"} if draft else {"open", "merging"}
        if (
            reconciled.get("status") not in expected_states
            or actual_source != head_ref
            or actual_target != base_ref
        ):
            raise ProviderError("SourceCraft pull request reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "pull_request",
            "number": reconciled.get("slug") or reconciled.get("id"),
            "title": reconciled.get("title", title),
            "state": reconciled.get("status"),
            "draft": reconciled.get("status") == "draft",
            "head_ref": actual_source,
            "base_ref": actual_target,
            "head_sha": (reconciled.get("source") or {}).get("sha"),
            "html_url": reconciled.get("web_url"),
            "reconciled": True,
        }
