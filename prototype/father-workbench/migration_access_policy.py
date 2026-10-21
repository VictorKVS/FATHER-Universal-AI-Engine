"""Provider-neutral migration access and branch-policy review."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def evaluate_access_policy(
    *,
    project_id: str,
    source: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not source.get("complete"):
        blockers.append("SOURCE_ACCESS_POLICY_INCOMPLETE")
    if not target.get("complete"):
        blockers.append("TARGET_ACCESS_POLICY_INCOMPLETE")

    if source.get("protected") is True and target.get("protected") is not True:
        blockers.append("TARGET_BRANCH_NOT_PROTECTED")

    source_force = source.get("force_push_allowed")
    target_force = target.get("force_push_allowed")
    if source_force is False and target_force is True:
        blockers.append("TARGET_FORCE_PUSH_WEAKER")

    source_delete = source.get("deletion_allowed")
    target_delete = target.get("deletion_allowed")
    if source_delete is False and target_delete is True:
        blockers.append("TARGET_DELETION_POLICY_WEAKER")

    source_reviews = source.get("review_required")
    target_reviews = target.get("review_required")
    if source_reviews is True:
        if target_reviews is False:
            blockers.append("TARGET_REVIEW_POLICY_WEAKER")
        elif target_reviews is None:
            blockers.append("TARGET_REVIEW_POLICY_UNKNOWN")

    source_code_owner = source.get("code_owner_review_required")
    target_code_owner = target.get("code_owner_review_required")
    if source_code_owner is True and target_code_owner is not True:
        blockers.append("TARGET_CODE_OWNER_POLICY_WEAKER_OR_UNKNOWN")

    source_checks = source.get("required_status_checks")
    target_checks = target.get("required_status_checks")
    if source_checks is True:
        if target_checks is False:
            blockers.append("TARGET_STATUS_CHECK_POLICY_WEAKER")
        elif target_checks is None:
            blockers.append("TARGET_STATUS_CHECK_POLICY_UNKNOWN")

    for item in source.get("limitations") or []:
        warnings.append(f"SOURCE:{item}")
    for item in target.get("limitations") or []:
        warnings.append(f"TARGET:{item}")

    # Normalization cannot prove semantic equivalence across providers.
    if source.get("provider") != target.get("provider"):
        warnings.append("CROSS_PROVIDER_SECURITY_REVIEW_REQUIRED")

    state = "PASS_WITH_REVIEW" if not blockers else "FAIL"
    payload = {
        "schema_version": "father.migration_access_policy.v0.1",
        "project_id": project_id,
        "source_provider": source.get("provider"),
        "target_provider": target.get("provider"),
        "source_repository": source.get("repository"),
        "target_repository": target.get("repository"),
        "branch": {
            "source": source.get("branch"),
            "target": target.get("branch"),
        },
        "state": state,
        "blockers": blockers,
        "warnings": warnings,
        "normalized": {
            "source": {
                key: source.get(key)
                for key in (
                    "protected",
                    "force_push_allowed",
                    "deletion_allowed",
                    "review_required",
                    "code_owner_review_required",
                    "required_status_checks",
                    "admin_enforcement",
                    "direct_push_restricted",
                )
            },
            "target": {
                key: target.get(key)
                for key in (
                    "protected",
                    "force_push_allowed",
                    "deletion_allowed",
                    "review_required",
                    "code_owner_review_required",
                    "required_status_checks",
                    "admin_enforcement",
                    "direct_push_restricted",
                )
            },
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
    payload["report_id"] = f"ACCESSPOL-{digest[:16].upper()}"
    payload["payload_sha256"] = digest
    return payload
