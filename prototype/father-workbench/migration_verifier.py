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


def verify_ref_inventory(
    *,
    project_id: str,
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not source.get("complete"):
        blockers.append("SOURCE_REF_INVENTORY_INCOMPLETE")
    if not target.get("complete"):
        blockers.append("TARGET_REF_INVENTORY_INCOMPLETE")

    source_default = source.get("default_branch")
    target_default = target.get("default_branch")
    if source_default != target_default:
        blockers.append("DEFAULT_BRANCH_MISMATCH")

    source_branches = dict(source.get("branches") or {})
    target_branches = dict(target.get("branches") or {})
    source_tags = dict(source.get("tags") or {})
    target_tags = dict(target.get("tags") or {})

    missing_branches = sorted(set(source_branches) - set(target_branches))
    extra_branches = sorted(set(target_branches) - set(source_branches))
    missing_tags = sorted(set(source_tags) - set(target_tags))
    extra_tags = sorted(set(target_tags) - set(source_tags))

    branch_sha_mismatch = {
        name: {
            "source": source_branches[name],
            "target": target_branches[name],
        }
        for name in sorted(set(source_branches) & set(target_branches))
        if source_branches[name] != target_branches[name]
    }
    tag_sha_mismatch = {
        name: {
            "source": source_tags[name],
            "target": target_tags[name],
        }
        for name in sorted(set(source_tags) & set(target_tags))
        if source_tags[name] != target_tags[name]
    }

    if missing_branches:
        blockers.append("TARGET_MISSING_BRANCHES")
    if extra_branches:
        blockers.append("TARGET_EXTRA_BRANCHES")
    if branch_sha_mismatch:
        blockers.append("BRANCH_SHA_MISMATCH")
    if missing_tags:
        blockers.append("TARGET_MISSING_TAGS")
    if extra_tags:
        blockers.append("TARGET_EXTRA_TAGS")
    if tag_sha_mismatch:
        blockers.append("TAG_SHA_MISMATCH")

    for item in source.get("limitations") or []:
        warnings.append(f"SOURCE:{item}")
    for item in target.get("limitations") or []:
        warnings.append(f"TARGET:{item}")

    state = "PASS" if not blockers else "FAIL"
    payload = {
        "schema_version": "father.provider_ref_parity.v0.1",
        "project_id": project_id,
        "source_provider": source.get("provider"),
        "target_provider": target.get("provider"),
        "source_repository": source.get("repository"),
        "target_repository": target.get("repository"),
        "state": state,
        "blockers": blockers,
        "warnings": warnings,
        "default_branch": {
            "source": source_default,
            "target": target_default,
            "match": source_default == target_default,
        },
        "counts": {
            "source_branches": len(source_branches),
            "target_branches": len(target_branches),
            "source_tags": len(source_tags),
            "target_tags": len(target_tags),
        },
        "differences": {
            "missing_branches": missing_branches,
            "extra_branches": extra_branches,
            "branch_sha_mismatch": branch_sha_mismatch,
            "missing_tags": missing_tags,
            "extra_tags": extra_tags,
            "tag_sha_mismatch": tag_sha_mismatch,
        },
    }
    digest = hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    payload["report_id"] = f"REFPARITY-{digest[:16].upper()}"
    payload["payload_sha256"] = digest
    return payload
