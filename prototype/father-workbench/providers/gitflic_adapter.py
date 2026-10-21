"""GitFlic provider adapter for the FATHER control plane."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from providers.base import ProviderError, validate_branch_name


class GitFlicAdapter:
    provider_id = "gitflic"
    write_actions = {"SCM.CREATE_BRANCH", "SCM.OPEN_CHANGE_REQUEST"}

    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._token = token if token is not None else os.getenv("FATHER_GITFLIC_TOKEN")
        self._base_url = (
            base_url if base_url is not None else os.getenv(
                "FATHER_GITFLIC_URL",
                "https://api.gitflic.ru",
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
            raise ValueError("GitFlic repository must be owner/project")
        return parts[0], parts[1]

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

    def _request(self, path: str, query: dict[str, str] | None = None) -> Any:
        url = self._base_url + path
        if query:
            url += "?" + urlencode(query)
        request = Request(url, headers=self._headers(), method="GET")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ProviderError(f"GitFlic HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitFlic network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitFlic returned invalid JSON") from None

    def _mutate(self, method: str, path: str, payload: dict[str, Any]) -> Any:
        if not self._token:
            raise ProviderError("GitFlic write credential unavailable")
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
            raise ProviderError(f"GitFlic HTTP {exc.code}") from None
        except URLError as exc:
            raise ProviderError(f"GitFlic network error: {exc.reason}") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("GitFlic returned invalid JSON") from None

    @staticmethod
    def _branch_sha(value: dict[str, Any]) -> str | None:
        return (value.get("lastCommit") or {}).get("hash")

    @staticmethod
    def _embedded(value: dict[str, Any], *names: str) -> list[dict[str, Any]]:
        embedded = value.get("_embedded") or {}
        for name in names:
            items = embedded.get(name)
            if isinstance(items, list):
                return items
        return []

    @staticmethod
    def _compact_mr(value: dict[str, Any]) -> dict[str, Any]:
        source = value.get("sourceBranch") or {}
        target = value.get("targetBranch") or {}
        status = (value.get("status") or {}).get("id")
        return {
            "number": value.get("localId"),
            "id": value.get("id"),
            "title": value.get("title"),
            "state": status,
            "draft": False,
            "html_url": value.get("url") or value.get("webUrl"),
            "head_sha": source.get("hash"),
            "source_branch": source.get("id") or source.get("title"),
            "base_ref": target.get("id") or target.get("title"),
            "updated_at": value.get("updatedAt"),
        }

    @staticmethod
    def _compact_pipeline(value: dict[str, Any]) -> dict[str, Any]:
        status = (
            value.get("status")
            or value.get("pipelineStatus")
            or value.get("state")
        )
        conclusion = None
        if isinstance(status, dict):
            status = status.get("id") or status.get("name")
        status_text = str(status or "").upper()
        if status_text in {"SUCCESS", "FAILED", "CANCELED", "CANCELLED", "SKIPPED"}:
            conclusion = status_text.lower()
            status = "completed"
        return {
            "id": value.get("id"),
            "name": value.get("name") or value.get("title"),
            "event": value.get("trigger") or value.get("source"),
            "status": status,
            "conclusion": conclusion,
            "head_sha": value.get("sha") or value.get("commitHash"),
            "html_url": value.get("url") or value.get("webUrl"),
            "created_at": value.get("createdAt"),
            "updated_at": value.get("updatedAt"),
        }

    def live_state(
        self,
        repository: str,
        branch: str,
        default_branch_hint: str | None = None,
    ) -> dict[str, Any]:
        owner, project_alias = self.split_repository(repository)
        root = f"/project/{quote(owner, safe='')}/{quote(project_alias, safe='')}"
        project = self._request(root)
        default_branch = (
            project.get("defaultBranch")
            or default_branch_hint
            or "master"
        )

        branch_data = self._request(
            f"{root}/branch",
            {"name": branch},
        )
        head_sha = self._branch_sha(branch_data)
        if not head_sha:
            raise ProviderError("GitFlic branch response has no head hash")

        compare = self._request(
            f"{root}/branch/compare",
            {"compare": branch, "base": default_branch},
        )
        mr_data = self._request(f"{root}/merge-request/list")
        all_mrs = self._embedded(
            mr_data,
            "mergeRequestModelList",
            "mergeRequestList",
        )
        mrs = [
            item
            for item in all_mrs
            if (
                ((item.get("sourceBranch") or {}).get("id") == branch)
                and ((item.get("status") or {}).get("id") == "OPENED")
            )
        ]

        pipeline_data = self._request(
            f"{root}/cicd/pipeline",
            {"branch": branch},
        )
        pipelines = self._embedded(
            pipeline_data,
            "restPipelineModelList",
            "pipelineList",
        )[:10]

        diffs = compare if isinstance(compare, list) else []
        return {
            "provider": self.provider_id,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "full_name": f"{owner}/{project.get('alias', project_alias)}",
                "private": project.get("private"),
                "default_branch": default_branch,
                "archived": project.get("archived"),
                "visibility": project.get("visibility"),
                "web_url": (
                    project.get("forkUrl")
                    or project.get("siteUrl")
                    or f"https://gitflic.ru/project/{owner}/{project_alias}"
                ),
            },
            "branch": {
                "name": branch,
                "head_sha": head_sha,
                "protected": branch_data.get("protected"),
            },
            "compare": {
                "status": "diverged" if diffs else "identical",
                "ahead_by": None,
                "behind_by": None,
                "total_commits": None,
                "changed_files": len(diffs),
            },
            "change_requests": [
                self._compact_mr(item) for item in mrs
            ],
            "checks": [],
            "combined_status": None,
            "workflow_runs": [
                self._compact_pipeline(item) for item in pipelines
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
        owner, project_alias = self.split_repository(repository)
        root = f"/project/{quote(owner, safe='')}/{quote(project_alias, safe='')}"

        created = self._mutate(
            "POST",
            f"{root}/branch",
            {
                "newBranch": branch_name,
                "originBranch": base_ref,
            },
        )
        created_sha = self._branch_sha(created)
        reconciled = self._request(
            f"{root}/branch",
            {"name": branch_name},
        )
        reconciled_sha = self._branch_sha(reconciled)
        if reconciled.get("name") != branch_name or not reconciled_sha:
            raise ProviderError("GitFlic branch reconciliation mismatch")
        if created_sha and created_sha != reconciled_sha:
            raise ProviderError("GitFlic branch SHA reconciliation mismatch")

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
        draft: bool = True,
    ) -> dict[str, Any]:
        if draft:
            raise ValueError(
                "GitFlic draft merge requests are not enabled by this adapter"
            )
        if not self._token:
            raise ProviderError("GitFlic write credential unavailable")

        title = title.strip()
        if not title or len(title) > 200:
            raise ValueError("Merge request title must be 1..200 characters")
        head_ref = validate_branch_name(head_ref)
        base_ref = validate_branch_name(base_ref)
        owner, project_alias = self.split_repository(repository)
        root = f"/project/{quote(owner, safe='')}/{quote(project_alias, safe='')}"

        project = self._request(root)
        project_id = project.get("id")
        if not project_id:
            raise ProviderError("GitFlic project response has no project id")

        created = self._mutate(
            "POST",
            f"{root}/merge-request",
            {
                "title": title,
                "description": body[:10000],
                "sourceBranch": {"id": head_ref},
                "targetBranch": {"id": base_ref},
                "sourceProject": {"id": project_id},
                "targetProject": {"id": project_id},
                "squashCommit": False,
                "removeSourceBranch": False,
            },
        )
        local_id = created.get("localId")
        if not isinstance(local_id, int):
            raise ProviderError("GitFlic merge request response has no localId")

        reconciled = self._request(
            f"{root}/merge-request/{local_id}"
        )
        source = reconciled.get("sourceBranch") or {}
        target = reconciled.get("targetBranch") or {}
        state = (reconciled.get("status") or {}).get("id")
        if (
            source.get("id") != head_ref
            or target.get("id") != base_ref
            or state != "OPENED"
        ):
            raise ProviderError("GitFlic merge request reconciliation mismatch")

        return {
            "provider": self.provider_id,
            "repository": repository,
            "change_request_type": "merge_request",
            "number": local_id,
            "id": reconciled.get("id"),
            "title": reconciled.get("title", title),
            "state": state,
            "draft": False,
            "head_ref": source.get("id"),
            "base_ref": target.get("id"),
            "head_sha": source.get("hash"),
            "html_url": reconciled.get("url") or reconciled.get("webUrl"),
            "reconciled": True,
        }
