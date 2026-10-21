"""Provider-neutral repository migration planning for FATHER."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _provider_by_id(registry: dict[str, Any], provider_id: str) -> dict[str, Any] | None:
    for provider in registry.get("providers", []):
        if provider.get("id") == provider_id:
            return provider
    return None


def _stable_plan_id(project_id: str, source: str, target: str) -> str:
    digest = hashlib.sha256(
        f"{project_id}|{source}|{target}".encode("utf-8")
    ).hexdigest()[:16].upper()
    return f"MIGPLAN-{digest}"


def build_migration_plan(
    project: dict[str, Any],
    target_provider: str,
    provider_registry: dict[str, Any],
) -> dict[str, Any]:
    project_id = str(project.get("project_id") or "")
    dev_platform = project.get("dev_platform") or {}
    source_provider = str(dev_platform.get("primary_provider") or "")
    target_provider = target_provider.strip()

    blockers: list[str] = []
    warnings: list[str] = []

    source = _provider_by_id(provider_registry, source_provider)
    target = _provider_by_id(provider_registry, target_provider)

    if not project_id:
        blockers.append("PROJECT_ID_REQUIRED")
    if not source_provider:
        blockers.append("SOURCE_PROVIDER_REQUIRED")
    if not target_provider:
        blockers.append("TARGET_PROVIDER_REQUIRED")
    if source_provider and target_provider and source_provider == target_provider:
        blockers.append("TARGET_EQUALS_SOURCE")
    if not source:
        blockers.append("SOURCE_PROVIDER_NOT_REGISTERED")
    if not target:
        blockers.append("TARGET_PROVIDER_NOT_REGISTERED")

    if source and str(source.get("adapter_status", "")).startswith("PLANNED"):
        blockers.append("SOURCE_ADAPTER_NOT_IMPLEMENTED")
    if target and str(target.get("adapter_status", "")).startswith("PLANNED"):
        blockers.append("TARGET_ADAPTER_NOT_IMPLEMENTED")

    if target and target.get("adapter_status") == "IMPLEMENTED_READ_ONLY":
        warnings.append("TARGET_WRITE_CAPABILITY_INCOMPLETE")

    # Physical transfer/cutover is deliberately not enabled yet.
    blockers.append("MIGRATION_EXECUTION_NOT_IMPLEMENTED")

    phases = [
        {
            "id": "MIG-01",
            "name": "Source inventory",
            "status": "READY" if source else "BLOCKED",
            "checks": [
                "repository identity",
                "default branch",
                "branches and tags",
                "HEAD hashes",
                "open change requests",
                "issues/work items",
                "pipelines/workflows",
                "packages/artifacts",
                "branch protection and access model",
            ],
        },
        {
            "id": "MIG-02",
            "name": "Target connectivity and repository preparation",
            "status": (
                "READY_FOR_CONFIGURATION"
                if target and not str(target.get("adapter_status", "")).startswith("PLANNED")
                else "BLOCKED"
            ),
            "checks": [
                "target provider adapter",
                "credential present",
                "target namespace",
                "target repository availability",
                "target visibility",
                "target default branch policy",
            ],
        },
        {
            "id": "MIG-03",
            "name": "Git object transfer",
            "status": "NOT_IMPLEMENTED",
            "checks": [
                "all refs transferred",
                "commit graph preserved",
                "tags preserved",
                "default branch preserved",
                "LFS/submodule requirements reviewed if applicable",
            ],
        },
        {
            "id": "MIG-04",
            "name": "Reference parity verification",
            "status": "PLANNED",
            "checks": [
                "branch names parity",
                "tag names parity",
                "branch HEAD SHA parity",
                "tag target SHA parity",
                "default branch parity",
            ],
        },
        {
            "id": "MIG-05",
            "name": "Metadata and DevOps mapping",
            "status": "PLANNED",
            "checks": [
                "PR/MR mapping",
                "issues/work items mapping",
                "reviewers/labels mapping",
                "CI/CD mapping",
                "packages/artifacts mapping",
                "webhooks/integrations mapping",
            ],
        },
        {
            "id": "MIG-06",
            "name": "Security and access verification",
            "status": "PLANNED",
            "checks": [
                "permissions",
                "branch protection",
                "required checks",
                "secrets recreated without exporting secret values",
                "audit integration",
                "retention requirements",
            ],
        },
        {
            "id": "MIG-07",
            "name": "Cutover",
            "status": "BLOCKED",
            "checks": [
                "migration evidence complete",
                "target live read PASS",
                "security review",
                "human approval",
                "switch primary provider",
                "source becomes mirror/historical/decommissioned",
            ],
        },
    ]

    evidence = [
        "SOURCE_PROVIDER_STATE",
        "SOURCE_REF_INVENTORY",
        "TARGET_PROVIDER_STATE",
        "TARGET_REF_INVENTORY",
        "REF_PARITY_REPORT",
        "CHANGE_REQUEST_MAPPING_REPORT",
        "WORK_ITEM_MAPPING_REPORT",
        "CI_CD_MAPPING_REPORT",
        "ACCESS_AND_BRANCH_POLICY_REPORT",
        "MIGRATION_SECURITY_REVIEW",
        "CUTOVER_APPROVAL",
        "POST_CUTOVER_PROVIDER_STATE",
    ]

    state = "BLOCKED" if blockers else "READY"
    return {
        "schema_version": "father.provider_migration_plan.v0.1",
        "plan_id": _stable_plan_id(project_id, source_provider, target_provider),
        "project_id": project_id,
        "source_provider": source_provider,
        "target_provider": target_provider,
        "source_repository": dev_platform.get("repository") or project.get("repository"),
        "source_branch": dev_platform.get("branch") or project.get("branch"),
        "state": state,
        "executable": False,
        "blockers": blockers,
        "warnings": warnings,
        "phases": phases,
        "required_evidence": evidence,
        "invariants": [
            "project_id does not change",
            "Manufacturing KB history does not change",
            "Project Memory remains linked to the same project",
            "secret values are never exported into migration evidence",
            "no switch-primary before parity and security evidence",
        ],
        "registry_digest": hashlib.sha256(
            json.dumps(
                provider_registry,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
    }
