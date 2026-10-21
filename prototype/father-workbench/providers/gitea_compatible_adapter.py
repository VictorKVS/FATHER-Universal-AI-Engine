"""Gitea-compatible Dev Platform adapter used by Gitea and Forgejo."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name


class GiteaCompatibleAdapter:
    provider_id = "gitea-compatible"
    env_prefix = "FATHER_GITEA"
    default_base_url = "https://gitea.com"

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        env_token = f"{self.env_prefix}_TOKEN"
        env_url = f"{self.env_prefix}_URL"
        self._token = token if token is not None else os.getenv(env_token)
        configured = (
            base_url
            if base_url is not None
            else os.getenv(env_url, self.default_base_url)
        )
        self._base_url = configured.rstrip("/")
        self._api_url = self._base_url + "/api/v1"
        self._timeout = timeout

    @property
    def can_write(self) -> bool:
        return bool(self._token)

    @staticmethod
    def split_repository(repository: str) -> tuple[str, str]:
        parts = [part for part in repository.strip().split("/") if part]
        if len(parts) != 2:
            raise ValueError("Repository must be owner/name")
        return parts[0], parts[1]

    @staticmethod
    def validate_branch_name(value: str) -> str:
        return validate_branch_name(value)

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FATHER-Control-Plane/0.1",
        }
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _request(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = self._api_url + path
        if query:
            url += "?" + urlencode(query)
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(
                f"{self.provider_id} HTTP {exc.code}"
            ) from None
        except URLError as exc:
            raise ProviderError(
                f"{self.provider_id} network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(
                f"{self.provider_id} returned invalid JSON"
            ) from None

    def _mutate(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
    ) -> Any:
        if not self._token:
            raise ProviderError(
                f"{self.provider_id} write credential unavailable"
            )
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self._api_url + path,
            data=body,
            headers=self._headers("application/json"),
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(
                f"{self.provider_id} HTTP {exc.code}"
            ) from None
        except URLError as exc:
            raise ProviderError(
                f"{self.provider_id} network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(
                f"{self.provider_id} returned invalid JSON"
            ) from None

    @staticmethod
    def _branch_sha(value: dict[str, Any]) -> str | None:
        commit = value.get("commit") or {}
        return commit.get("id") or commit.get("sha")

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
            "head_sha": value.get("sha") or head.get("sha"),
            "source_branch": head.get("ref"),
            "base_ref": base.get("ref"),
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
            "name": value.get("name") or value.get("display_title"),
            "event": value.get("event"),
            "status": status,
            "conclusion": conclusion,
            "head_sha": value.get("head_sha"),
            "html_url": value.get("html_url"),
            "created_at": value.get("created_at"),
            "updated_at": value.get("updated_at"),
        }

    def ref_inventory(self, repository: str) -> dict[str, Any]:
        owner, name = self.split_repository(repository)
        root = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        repo = self._request(root)
        branches: dict[str, str] = {}
        tags: dict[str, str] = {}
        limitations: list[str] = []

        for page in range(1, 201):
            items = self._request(
                f"{root}/branches",
                {"limit": "50", "page": str(page)},
            )
            if not isinstance(items, list):
                raise ProviderError(
                    f"{self.provider_id} branch inventory invalid"
                )
            for item in items:
                sha = self._branch_sha(item)
                if item.get("name") and sha:
                    branches[str(item["name"])] = str(sha)
            if len(items) < 50:
                break
        else:
            limitations.append("BRANCH_PAGINATION_LIMIT_REACHED")

        for page in range(1, 201):
            items = self._request(
                f"{root}/tags",
                {"limit": "50", "page": str(page)},
            )
            if not isinstance(items, list):
                raise ProviderError(
                    f"{self.provider_id} tag inventory invalid"
                )
            for item in items:
                sha = (item.get("commit") or {}).get("sha") or item.get("id")
                if item.get("name") and sha:
                    tags[str(item["name"])] = str(sha)
            if len(items) < 50:
                break
        else:
            limitations.append("TAG_PAGINATION_LIMIT_REACHED")

        return {
            "provider": self.provider_id,
            "repository": repo.get("full_name", repository),
            "default_branch": repo.get("default_branch"),
            "branches": branches,
            "tags": tags,
            "complete": not limitations,
            "limitations": limitations,
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        owner, name = self.split_repository(repository)
        root = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"
        repo = self._request(root)
        default_branch = (
            repo.get("default_branch")
            or default_branch_hint
            or "main"
        )

        branch_data = self._request(
            f"{root}/branches/{quote(branch, safe='')}"
        )
        head_sha = self._branch_sha(branch_data)
        if not head_sha:
            raise ProviderError(
                f"{self.provider_id} branch response has no head SHA"
            )

        compare = self._request(
            f"{root}/compare/"
            f"{quote(default_branch + '...' + branch, safe='')}"
        )
        pulls = self._request(
            f"{root}/pulls",
            {"state": "open", "limit": "50"},
        )
        try:
            runs = self._request(
                f"{root}/actions/runs",
                {"limit": "10"},
            )
        except ProviderError:
            runs = {"workflow_runs": []}

        pull_items = pulls if isinstance(pulls, list) else []
        pull_items = [
            item
            for item in pull_items
            if (item.get("head") or {}).get("ref") == branch
        ]
        run_items = []
        if isinstance(runs, dict):
            run_items = runs.get("workflow_runs") or runs.get("runs") or []
        elif isinstance(runs, list):
            run_items = runs

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
                "status": (
                    "ahead"
                    if commits
                    else "identical"
                ),
                "ahead_by": len(commits),
                "behind_by": None,
                "total_commits": compare.get(
                    "total_commits",
                    len(commits),
                ) if isinstance(compare, dict) else None,
            },
            "change_requests": [
                self._compact_pull(item) for item in pull_items
            ],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_run(item)
                for item in run_items
                if not item.get("head_branch")
                or item.get("head_branch") == branch
            ][:10],
        }

    def create_branch(
        self,
        repository: str,
        branch_name: str,
        base_ref: str,
    ) -> dict[str, Any]:
        branch_name = self.validate_branch_name(branch_name)
        base_ref = self.validate_branch_name(base_ref)
        owner, name = self.split_repository(repository)
        root = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"

        created = self._mutate(
            "POST",
            f"{root}/branches",
            {
                "new_branch_name": branch_name,
                "old_ref_name": base_ref,
            },
        )
        created_sha = self._branch_sha(created)

        reconciled = self._request(
            f"{root}/branches/{quote(branch_name, safe='')}"
        )
        reconciled_sha = self._branch_sha(reconciled)
        if reconciled.get("name") != branch_name or not reconciled_sha:
            raise ProviderError(
                f"{self.provider_id} branch reconciliation mismatch"
            )
        if created_sha and created_sha != reconciled_sha:
            raise ProviderError(
                f"{self.provider_id} branch SHA reconciliation mismatch"
            )

        return {
            "provider": self.provider_id,
            "repository": repository,
            "branch": branch_name,
            "base_ref": base_ref,
            "head_sha": reconciled_sha,
            "provider_created_sha": created_sha,
            "reconciled": True,
        }

    def open_change_request(
        self,
        repository: str,
        title: str,
        head_ref: str,
        base_ref: str,
        body: str = "",
        draft: bool = False,
    ) -> dict[str, Any]:
        if draft:
            raise ValueError(
                f"{self.provider_id} draft PR is not enabled by FATHER"
            )
        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Pull request title must be 1..200 characters")
        head_ref = self.validate_branch_name(head_ref)
        base_ref = self.validate_branch_name(base_ref)
        owner, name = self.split_repository(repository)
        root = f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"

        created = self._mutate(
            "POST",
            f"{root}/pulls",
            {
                "title": title,
                "body": body[:10000],
                "head": head_ref,
                "base": base_ref,
            },
        )
        number = created.get("number")
        if not isinstance(number, int):
            raise ProviderError(
                f"{self.provider_id} pull request response has no number"
            )

        reconciled = self._request(f"{root}/pulls/{number}")
        actual_head = (reconciled.get("head") or {}).get("ref")
        actual_base = (reconciled.get("base") or {}).get("ref")
        if (
            reconciled.get("state") != "open"
            or actual_head != head_ref
            or actual_base != base_ref
        ):
            raise ProviderError(
                f"{self.provider_id} pull request reconciliation mismatch"
            )

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "pull_request",
            "number": number,
            "title": reconciled.get("title", title),
            "state": reconciled.get("state"),
            "draft": False,
            "head_ref": actual_head,
            "base_ref": actual_base,
            "head_sha": reconciled.get("sha")
                or (reconciled.get("head") or {}).get("sha"),
            "html_url": reconciled.get("html_url"),
            "reconciled": True,
        }
