"""Bitbucket Cloud provider adapter for FATHER."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name


class BitbucketAdapter:
    provider_id = "bitbucket"

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv(
            "FATHER_BITBUCKET_TOKEN"
        )
        self._base_url = (
            base_url
            if base_url is not None
            else os.getenv(
                "FATHER_BITBUCKET_URL",
                "https://api.bitbucket.org/2.0",
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
            raise ValueError("Bitbucket repository must be workspace/repo")
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

    def _request(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = self._base_url + path
        if query:
            url += "?" + urlencode(query)
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(f"Bitbucket HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(
                f"Bitbucket network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("Bitbucket returned invalid JSON") from None

    def _mutate(
        self,
        method: str,
        path: str,
        payload: dict[str, Any],
    ) -> Any:
        if not self._token:
            raise ProviderError("Bitbucket write credential unavailable")
        request = Request(
            self._base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers("application/json"),
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(f"Bitbucket HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(
                f"Bitbucket network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("Bitbucket returned invalid JSON") from None

    @staticmethod
    def _branch_sha(value: dict[str, Any]) -> str | None:
        return (value.get("target") or {}).get("hash")

    @staticmethod
    def _compact_pull(value: dict[str, Any]) -> dict[str, Any]:
        source = value.get("source") or {}
        destination = value.get("destination") or {}
        return {
            "number": value.get("id"),
            "title": value.get("title"),
            "state": value.get("state"),
            "draft": value.get("draft"),
            "html_url": ((value.get("links") or {}).get("html") or {}).get(
                "href"
            ),
            "head_sha": (source.get("commit") or {}).get("hash"),
            "source_branch": (source.get("branch") or {}).get("name"),
            "base_ref": (destination.get("branch") or {}).get("name"),
            "updated_at": value.get("updated_on"),
        }

    @staticmethod
    def _compact_pipeline(value: dict[str, Any]) -> dict[str, Any]:
        state = value.get("state") or {}
        result = state.get("result") or {}
        name = (result.get("name") or state.get("name") or "").lower()
        conclusion = None
        status = str(state.get("name") or "").lower()
        if name in {"successful", "failed", "stopped", "error"}:
            conclusion = (
                "success" if name == "successful"
                else "cancelled" if name == "stopped"
                else "failure"
            )
            status = "completed"
        target = value.get("target") or {}
        commit = target.get("commit") or {}
        return {
            "id": value.get("uuid") or value.get("build_number"),
            "name": value.get("build_number"),
            "event": target.get("type"),
            "status": status or None,
            "conclusion": conclusion,
            "head_sha": commit.get("hash"),
            "html_url": ((value.get("links") or {}).get("html") or {}).get(
                "href"
            ),
            "created_at": value.get("created_on"),
            "updated_at": value.get("completed_on"),
        }

    def ref_inventory(self, repository: str) -> dict[str, Any]:
        workspace, repo_slug = self.split_repository(repository)
        root = (
            f"/repositories/{quote(workspace, safe='')}/"
            f"{quote(repo_slug, safe='')}"
        )
        repo = self._request(root)
        branches: dict[str, str] = {}
        tags: dict[str, str] = {}
        limitations: list[str] = []

        for page in range(1, 101):
            data = self._request(
                f"{root}/refs/branches",
                {"pagelen": "100", "page": str(page)},
            )
            if not isinstance(data, dict):
                raise ProviderError("Bitbucket branch inventory invalid")
            values = data.get("values", [])
            for item in values:
                sha = self._branch_sha(item)
                if item.get("name") and sha:
                    branches[str(item["name"])] = str(sha)
            if not data.get("next"):
                break
        else:
            limitations.append("BRANCH_PAGINATION_LIMIT_REACHED")

        for page in range(1, 101):
            data = self._request(
                f"{root}/refs/tags",
                {"pagelen": "100", "page": str(page)},
            )
            if not isinstance(data, dict):
                raise ProviderError("Bitbucket tag inventory invalid")
            values = data.get("values", [])
            for item in values:
                sha = (item.get("target") or {}).get("hash")
                if item.get("name") and sha:
                    tags[str(item["name"])] = str(sha)
            if not data.get("next"):
                break
        else:
            limitations.append("TAG_PAGINATION_LIMIT_REACHED")

        return {
            "provider": self.provider_id,
            "repository": repo.get("full_name", repository),
            "default_branch": (repo.get("mainbranch") or {}).get("name"),
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
        workspace, repo_slug = self.split_repository(repository)
        root = (
            f"/repositories/{quote(workspace, safe='')}/"
            f"{quote(repo_slug, safe='')}"
        )
        repo = self._request(root)
        default_branch = (
            ((repo.get("mainbranch") or {}).get("name"))
            or default_branch_hint
            or "main"
        )
        branch_data = self._request(
            f"{root}/refs/branches/{quote(branch, safe='')}"
        )
        head_sha = self._branch_sha(branch_data)
        if not head_sha:
            raise ProviderError("Bitbucket branch response has no head hash")

        pulls = self._request(
            f"{root}/pullrequests",
            {"state": "OPEN", "pagelen": "50"},
        )
        pipelines = self._request(
            f"{root}/pipelines",
            {"pagelen": "10", "sort": "-created_on"},
        )

        pull_items = pulls.get("values", []) if isinstance(pulls, dict) else []
        pull_items = [
            item
            for item in pull_items
            if ((item.get("source") or {}).get("branch") or {}).get("name")
            == branch
        ]
        run_items = (
            pipelines.get("values", [])
            if isinstance(pipelines, dict)
            else []
        )
        run_items = [
            item
            for item in run_items
            if not ((item.get("target") or {}).get("ref_name"))
            or (item.get("target") or {}).get("ref_name") == branch
        ]

        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": repo.get("full_name", repository),
                "private": repo.get("is_private"),
                "default_branch": default_branch,
                "archived": None,
                "visibility": "private" if repo.get("is_private") else "public",
                "web_url": ((repo.get("links") or {}).get("html") or {}).get(
                    "href"
                ),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": None,
            },
            "compare": {
                "status": "UNKNOWN",
                "ahead_by": None,
                "behind_by": None,
                "total_commits": None,
                "note": "Bitbucket adapter does not infer ahead/behind without a verified commit-distance contract.",
            },
            "change_requests": [
                self._compact_pull(item) for item in pull_items
            ],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_pipeline(item) for item in run_items
            ],
        }

    def create_branch(
        self,
        repository: str,
        branch_name: str,
        base_ref: str,
    ) -> dict[str, Any]:
        branch_name = validate_branch_name(branch_name)
        base_ref = validate_branch_name(base_ref)
        workspace, repo_slug = self.split_repository(repository)
        root = (
            f"/repositories/{quote(workspace, safe='')}/"
            f"{quote(repo_slug, safe='')}"
        )

        base = self._request(
            f"{root}/refs/branches/{quote(base_ref, safe='')}"
        )
        base_sha = self._branch_sha(base)
        if not base_sha:
            raise ProviderError("Bitbucket base branch has no head hash")

        created = self._mutate(
            "POST",
            f"{root}/refs/branches",
            {
                "name": branch_name,
                "target": {"hash": base_sha},
            },
        )
        reconciled = self._request(
            f"{root}/refs/branches/{quote(branch_name, safe='')}"
        )
        reconciled_sha = self._branch_sha(reconciled)
        if reconciled.get("name") != branch_name:
            raise ProviderError("Bitbucket branch reconciliation mismatch")
        if reconciled_sha != base_sha:
            raise ProviderError("Bitbucket branch SHA reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "branch": branch_name,
            "base_ref": base_ref,
            "head_sha": reconciled_sha,
            "provider_created_sha": self._branch_sha(created),
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
        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Pull request title must be 1..200 characters")
        head_ref = validate_branch_name(head_ref)
        base_ref = validate_branch_name(base_ref)
        workspace, repo_slug = self.split_repository(repository)
        root = (
            f"/repositories/{quote(workspace, safe='')}/"
            f"{quote(repo_slug, safe='')}"
        )

        created = self._mutate(
            "POST",
            f"{root}/pullrequests",
            {
                "title": title,
                "description": body[:10000],
                "draft": bool(draft),
                "source": {"branch": {"name": head_ref}},
                "destination": {"branch": {"name": base_ref}},
            },
        )
        number = created.get("id")
        if not isinstance(number, int):
            raise ProviderError("Bitbucket pull request response has no id")

        reconciled = self._request(f"{root}/pullrequests/{number}")
        actual_head = (
            ((reconciled.get("source") or {}).get("branch") or {}).get("name")
        )
        actual_base = (
            ((reconciled.get("destination") or {}).get("branch") or {}).get(
                "name"
            )
        )
        if (
            reconciled.get("state") != "OPEN"
            or actual_head != head_ref
            or actual_base != base_ref
        ):
            raise ProviderError("Bitbucket pull request reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "pull_request",
            "number": number,
            "title": reconciled.get("title", title),
            "state": reconciled.get("state"),
            "draft": bool(reconciled.get("draft")),
            "head_ref": actual_head,
            "base_ref": actual_base,
            "head_sha": (
                (reconciled.get("source") or {}).get("commit") or {}
            ).get("hash"),
            "html_url": (
                ((reconciled.get("links") or {}).get("html") or {}).get(
                    "href"
                )
            ),
            "reconciled": True,
        }
