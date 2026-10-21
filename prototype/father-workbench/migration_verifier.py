"""Provider-neutral migration parity verification."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def verification_id(
    project_id: str,
    source_provider: str,
    target_provider: str,
    source_head: str,
    target_head: str,
) -> str:
    digest = hashlib.sha256(
        "|".join([
            project_id,
            source_provider,
            target_provider,
            source_head,
            target_head,
        ]).encode("utf-8")
    ).hexdigest()[:16].upper()
    return f"MIGVERIFY-{digest}"


def verify_provider_parity(
    *,
    project_id: str,
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    source_head = str((source.get("branch") or {}).get("head_sha") or "")
    target_head = str((target.get("branch") or {}).get("head_sha") or "")
    source_branch = str((source.get("branch") or {}).get("name") or "")
    target_branch = str((target.get("branch") or {}).get("name") or "")
    source_provider = str(source.get("provider") or "")
    target_provider = str(target.get("provider") or "")

    blockers: list[str] = []
    if not source_head:
        blockers.append("SOURCE_HEAD_UNAVAILABLE")
    if not target_head:
        blockers.append("TARGET_HEAD_UNAVAILABLE")
    if source_branch != target_branch:
        blockers.append("BRANCH_NAME_MISMATCH")
    if source_head and target_head and source_head != target_head:
        blockers.append("HEAD_SHA_MISMATCH")

    state = "PASS" if not blockers else "FAIL"
    payload = {
        "schema_version": "father.provider_migration_verification.v0.1",
        "project_id": project_id,
        "source_provider": source_provider,
        "target_provider": target_provider,
        "source_repository": (source.get("repository") or {}).get("full_name"),
        "target_repository": (target.get("repository") or {}).get("full_name"),
        "source_branch": source_branch,
        "target_branch": target_branch,
        "source_head_sha": source_head,
        "target_head_sha": target_head,
        "state": state,
        "blockers": blockers,
        "checks": {
            "branch_name_parity": source_branch == target_branch,
            "head_sha_parity": bool(source_head) and source_head == target_head,
        },
    }
    payload["verification_id"] = verification_id(
        project_id,
        source_provider,
        target_provider,
        source_head,
        target_head,
    )
    payload["payload_sha256"] = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return payload
