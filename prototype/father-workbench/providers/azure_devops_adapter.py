"""Azure DevOps Repos provider adapter for FATHER."""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name

ZERO_SHA = "0" * 40


class AzureDevOpsAdapter:
    provider_id = "azure_devops"

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv(
            "FATHER_AZURE_DEVOPS_TOKEN"
        )
        self._base_url = (
            base_url
            if base_url is not None
            else os.getenv(
                "FATHER_AZURE_DEVOPS_URL",
                "https://dev.azure.com",
            )
        ).rstrip("/")
        self._timeout = timeout

    @property
    def can_write(self) -> bool:
        return bool(self._token)

    @staticmethod
    def split_repository(repository: str) -> tuple[str, str, str]:
        parts = [part for part in repository.strip().split("/") if part]
        if len(parts) != 3:
            raise ValueError(
                "Azure DevOps repository must be organization/project/repository"
            )
        return parts[0], parts[1], parts[2]

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FATHER-Control-Plane/0.1",
        }
        if self._token:
            basic = base64.b64encode(
                f":{self._token}".encode("utf-8")
            ).decode("ascii")
            headers["Authorization"] = f"Basic {basic}"
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _root(self, repository: str) -> tuple[str, str, str, str]:
        org, project, repo_name = self.split_repository(repository)
        root = (
            f"/{quote(org, safe='')}/{quote(project, safe='')}"
            f"/_apis/git/repositories/{quote(repo_name, safe='')}"
        )
        return org, project, repo_name, root

    def _request(
        self,
        path: str,
        query: dict[str, str] | None = None,
    ) -> Any:
        params = {"api-version": "7.1"}
        if query:
            params.update(query)
        url = self._base_url + path + "?" + urlencode(params)
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(
                f"Azure DevOps HTTP {exc.code}"
            ) from None
        except URLError as exc:
            raise ProviderError(
                f"Azure DevOps network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(
                "Azure DevOps returned invalid JSON"
            ) from None

    def _mutate(
        self,
        method: str,
        path: str,
        payload: Any,
    ) -> Any:
        if not self._token:
            raise ProviderError(
                "Azure DevOps write credential unavailable"
            )
        url = self._base_url + path + "?api-version=7.1"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers("application/json"),
            method=method,
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise ProviderError(
                f"Azure DevOps HTTP {exc.code}"
            ) from None
        except URLError as exc:
            raise ProviderError(
                f"Azure DevOps network error: {exc.reason}"
            ) from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(
                "Azure DevOps returned invalid JSON"
            ) from None

    @staticmethod
    def _refs_value(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            values = data.get("value", [])
            return values if isinstance(values, list) else []
        return []

    @staticmethod
    def _compact_pull(value: dict[str, Any]) -> dict[str, Any]:
        return {
            "number": value.get("pullRequestId"),
            "title": value.get("title"),
            "state": value.get("status"),
            "draft": value.get("isDraft"),
            "html_url": (
                ((value.get("_links") or {}).get("web") or {}).get("href")
            ),
            "head_sha": (value.get("lastMergeSourceCommit") or {}).get(
                "commitId"
            ),
            "source_branch": str(
                value.get("sourceRefName") or ""
            ).removeprefix("refs/heads/"),
            "base_ref": str(
                value.get("targetRefName") or ""
            ).removeprefix("refs/heads/"),
            "updated_at": value.get("creationDate"),
        }

    def _ref(
        self,
        root: str,
        branch: str,
        *,
        include_statuses: bool = False,
    ) -> dict[str, Any]:
        params = {
            "filter": f"heads/{branch}",
            "$top": "10",
        }
        if include_statuses:
            params["includeStatuses"] = "true"
            params["latestStatusesOnly"] = "true"
        data = self._request(f"{root}/refs", params)
        expected = f"refs/heads/{branch}"
        for item in self._refs_value(data):
            if item.get("name") == expected:
                return item
        raise ProviderError(f"Azure DevOps branch not found: {branch}")

    def ref_inventory(self, repository: str) -> dict[str, Any]:
        _org, _project, _repo_name, root = self._root(repository)
        repo = self._request(root)
        branches_data = self._request(
            f"{root}/refs",
            {"filter": "heads/", "$top": "1000"},
        )
        tags_data = self._request(
            f"{root}/refs",
            {"filter": "tags/", "$top": "1000"},
        )
        branch_values = self._refs_value(branches_data)
        tag_values = self._refs_value(tags_data)
        branches = {
            str(item["name"]).removeprefix("refs/heads/"): str(item["objectId"])
            for item in branch_values
            if item.get("name") and item.get("objectId")
        }
        tags = {
            str(item["name"]).removeprefix("refs/tags/"): str(item["objectId"])
            for item in tag_values
            if item.get("name") and item.get("objectId")
        }
        limitations: list[str] = []
        if len(branch_values) >= 1000:
            limitations.append("BRANCH_INVENTORY_MAY_BE_TRUNCATED")
        if len(tag_values) >= 1000:
            limitations.append("TAG_INVENTORY_MAY_BE_TRUNCATED")
        return {
            "provider": self.provider_id,
            "repository": repository,
            "default_branch": str(
                repo.get("defaultBranch") or ""
            ).removeprefix("refs/heads/") or None,
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
        _org, _project, _repo_name, root = self._root(repository)
        repo = self._request(root)
        default_branch = str(
            repo.get("defaultBranch")
            or (
                "refs/heads/" + default_branch_hint
                if default_branch_hint
                else "refs/heads/main"
            )
        ).removeprefix("refs/heads/")

        ref = self._ref(root, branch, include_statuses=True)
        head_sha = ref.get("objectId")
        if not head_sha:
            raise ProviderError(
                "Azure DevOps branch response has no objectId"
            )

        pulls = self._request(
            f"{root}/pullrequests",
            {
                "searchCriteria.status": "active",
                "searchCriteria.sourceRefName": f"refs/heads/{branch}",
            },
        )
        pull_items = self._refs_value(pulls)
        statuses = ref.get("statuses") or []
        checks = [
            {
                "id": item.get("id"),
                "name": (
                    (item.get("context") or {}).get("name")
                    or (item.get("context") or {}).get("genre")
                ),
                "status": item.get("state"),
                "conclusion": item.get("state"),
                "details_url": item.get("targetUrl"),
                "started_at": item.get("creationDate"),
                "completed_at": item.get("updatedDate"),
            }
            for item in statuses
        ]

        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": repository,
                "private": True,
                "default_branch": default_branch,
                "archived": repo.get("isDisabled"),
                "visibility": "organization",
                "web_url": repo.get("webUrl") or repo.get("remoteUrl"),
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
                "note": "Azure Repos adapter keeps branch-distance UNKNOWN until an explicit commit-distance contract is wired.",
            },
            "change_requests": [
                self._compact_pull(item) for item in pull_items
            ],
            "checks": checks,
            "combined_status": None,
            "workflow_runs": [],
        }

    def create_branch(
        self,
        repository: str,
        branch_name: str,
        base_ref: str,
    ) -> dict[str, Any]:
        branch_name = validate_branch_name(branch_name)
        base_ref = validate_branch_name(base_ref)
        _org, _project, _repo_name, root = self._root(repository)

        base = self._ref(root, base_ref)
        base_sha = base.get("objectId")
        if not base_sha:
            raise ProviderError("Azure DevOps base ref has no objectId")

        created = self._mutate(
            "POST",
            f"{root}/refs",
            [{
                "name": f"refs/heads/{branch_name}",
                "oldObjectId": ZERO_SHA,
                "newObjectId": base_sha,
            }],
        )
        results = self._refs_value(created)
        result = results[0] if results else {}
        if not result.get("success"):
            raise ProviderError(
                "Azure DevOps ref update was not successful"
            )

        reconciled = self._ref(root, branch_name)
        reconciled_sha = reconciled.get("objectId")
        if reconciled_sha != base_sha:
            raise ProviderError(
                "Azure DevOps branch reconciliation mismatch"
            )

        return {
            "provider": self.provider_id,
            "repository": repository,
            "branch": branch_name,
            "base_ref": base_ref,
            "head_sha": reconciled_sha,
            "provider_created_sha": result.get("newObjectId"),
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
        _org, _project, _repo_name, root = self._root(repository)

        created = self._mutate(
            "POST",
            f"{root}/pullrequests",
            {
                "sourceRefName": f"refs/heads/{head_ref}",
                "targetRefName": f"refs/heads/{base_ref}",
                "title": title,
                "description": body[:4000],
                "isDraft": bool(draft),
            },
        )
        number = created.get("pullRequestId")
        if not isinstance(number, int):
            raise ProviderError(
                "Azure DevOps pull request response has no id"
            )

        reconciled = self._request(f"{root}/pullrequests/{number}")
        actual_head = str(
            reconciled.get("sourceRefName") or ""
        ).removeprefix("refs/heads/")
        actual_base = str(
            reconciled.get("targetRefName") or ""
        ).removeprefix("refs/heads/")
        if (
            reconciled.get("status") != "active"
            or actual_head != head_ref
            or actual_base != base_ref
        ):
            raise ProviderError(
                "Azure DevOps pull request reconciliation mismatch"
            )

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "pull_request",
            "number": number,
            "title": reconciled.get("title", title),
            "state": reconciled.get("status"),
            "draft": bool(reconciled.get("isDraft")),
            "head_ref": actual_head,
            "base_ref": actual_base,
            "head_sha": (
                reconciled.get("lastMergeSourceCommit") or {}
            ).get("commitId"),
            "html_url": (
                ((reconciled.get("_links") or {}).get("web") or {}).get(
                    "href"
                )
            ),
            "reconciled": True,
        }
