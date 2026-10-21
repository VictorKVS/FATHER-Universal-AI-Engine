"""Evidence-oriented project health assessment for FATHER."""

from __future__ import annotations

from typing import Any


PASS_STATES = {"PASS", "READY", "READY_FOR_ARCHITECTURE", "SUCCESS"}
BLOCK_STATES = {"BLOCKED", "FAIL", "FAILED", "CANCELLED"}
PROGRESS_STATES = {
    "IN_PROGRESS",
    "DEVELOPMENT",
    "SECURITY_INTAKE",
    "PRODUCT_DISCOVERY",
    "WAITING",
    "NOT_READY",
    "BACKFILL_REQUIRED",
    "LEGACY_BASELINE",
}


def normalize(value: Any) -> str:
    return str(value or "UNKNOWN").strip().upper()


def current_stage_record(
    state: dict[str, Any],
) -> dict[str, Any] | None:
    current = str(state.get("current_stage") or "")
    for stage in state.get("stages", []):
        if str(stage.get("id") or "") == current:
            return stage
    return None


def document_dimension(state: dict[str, Any]) -> dict[str, Any]:
    summary = state.get("document_summary") or {}
    done = int(summary.get("done") or 0)
    total = int(summary.get("total") or 0)
    if total <= 0:
        status = "TBD"
    elif done >= total:
        status = "PASS"
    elif done > 0:
        status = "IN_PROGRESS"
    else:
        status = "NOT_STARTED"
    return {
        "status": status,
        "done": done,
        "total": total,
        "blocker": False,
    }


def gate_dimension(
    project: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    stage = current_stage_record(state) or {}
    stage_gate = normalize(stage.get("gate"))
    pre_design = normalize(project.get("pre_design_gate"))
    hard = stage_gate in BLOCK_STATES or pre_design == "BLOCKED"
    return {
        "status": "BLOCKED" if hard else stage_gate,
        "current_stage": state.get("current_stage"),
        "stage_gate": stage_gate,
        "pre_design_gate": pre_design,
        "blocker": hard,
    }


def security_dimension(project: dict[str, Any]) -> dict[str, Any]:
    status = normalize(project.get("security_gate"))
    return {
        "status": status,
        "blocker": status in BLOCK_STATES,
    }


def devsecops_dimension(
    devsecops: dict[str, Any] | None,
) -> dict[str, Any]:
    if not devsecops:
        return {
            "status": "UNKNOWN",
            "blocker": False,
            "reason": "CURRENT_HEAD_DEVSECOPS_NOT_EVALUATED",
        }
    status = normalize(devsecops.get("status"))
    return {
        "status": status,
        "head_sha": devsecops.get("head_sha"),
        "blocker": status in BLOCK_STATES,
        "blockers": list(devsecops.get("blockers") or []),
    }


def evidence_dimension(
    state: dict[str, Any],
    evidence_count: int,
) -> dict[str, Any]:
    declared = normalize(state.get("evidence_status"))
    return {
        "status": declared,
        "count": int(evidence_count),
        "blocker": declared in BLOCK_STATES,
    }


def provider_dimension(
    bindings: dict[str, Any],
) -> dict[str, Any]:
    primary = bindings.get("primary") or {}
    health = bindings.get("last_switch_health") or {}
    health_status = normalize(health.get("status"))
    blockers = list(health.get("blockers") or [])
    if not primary.get("provider"):
        return {
            "status": "BLOCKED",
            "blocker": True,
            "blockers": ["PRIMARY_PROVIDER_NOT_BOUND"],
        }
    if health and (
        "DEGRADED" in health_status
        or health.get("rollback_recommended") is True
    ):
        return {
            "status": "DEGRADED",
            "provider": primary.get("provider"),
            "repository": primary.get("repository"),
            "branch": primary.get("branch"),
            "blocker": True,
            "blockers": blockers or ["PROVIDER_SWITCH_HEALTH_DEGRADED"],
            "rollback_recommended": bool(
                health.get("rollback_recommended")
            ),
        }
    return {
        "status": (
            health_status
            if health
            else "BOUND"
        ),
        "provider": primary.get("provider"),
        "repository": primary.get("repository"),
        "branch": primary.get("branch"),
        "blocker": False,
        "blockers": blockers,
        "rollback_recommended": False,
    }


def runtime_dimension(project: dict[str, Any]) -> dict[str, Any]:
    status = normalize(project.get("runtime_status"))
    return {
        "status": status,
        "blocker": status in BLOCK_STATES,
    }


def budget_dimension(project: dict[str, Any]) -> dict[str, Any]:
    summary = project.get("budget_summary")
    if not summary:
        return {
            "status": "TBD",
            "blocker": False,
        }
    if isinstance(summary, dict):
        status = normalize(summary.get("status"))
        return {
            "status": status,
            "blocker": status in BLOCK_STATES,
            "summary": summary,
        }
    return {
        "status": "REPORTED",
        "blocker": False,
        "summary": summary,
    }


def assess_project_health(
    *,
    project: dict[str, Any],
    state: dict[str, Any],
    bindings: dict[str, Any],
    devsecops: dict[str, Any] | None,
    evidence_count: int,
) -> dict[str, Any]:
    dimensions = {
        "documents": document_dimension(state),
        "gates": gate_dimension(project, state),
        "security": security_dimension(project),
        "devsecops": devsecops_dimension(devsecops),
        "evidence": evidence_dimension(state, evidence_count),
        "provider": provider_dimension(bindings),
        "runtime": runtime_dimension(project),
        "budget": budget_dimension(project),
    }

    hard_blockers: list[str] = []
    for name, dimension in dimensions.items():
        if dimension.get("blocker"):
            blockers = dimension.get("blockers") or []
            if blockers:
                hard_blockers.extend(
                    f"{name.upper()}:{item}" for item in blockers
                )
            else:
                hard_blockers.append(
                    f"{name.upper()}:{dimension.get('status')}"
                )

    release_prerequisites = {
        "pre_design_gate": normalize(project.get("pre_design_gate")),
        "architecture_gate": normalize(project.get("architecture_gate")),
        "security_gate": normalize(project.get("security_gate")),
        "devsecops": dimensions["devsecops"]["status"],
        "provider": dimensions["provider"]["status"],
    }
    release_ready = (
        not hard_blockers
        and release_prerequisites["pre_design_gate"] == "PASS"
        and release_prerequisites["architecture_gate"] == "PASS"
        and release_prerequisites["security_gate"] == "PASS"
        and release_prerequisites["devsecops"] == "PASS"
        and dimensions["provider"]["status"] not in {
            "DEGRADED",
            "BLOCKED",
            "UNKNOWN",
        }
    )

    if hard_blockers:
        overall = "BLOCKED"
    elif release_ready:
        overall = "RELEASE_READY"
    else:
        overall = "IN_PROGRESS"

    return {
        "schema_version": "father.project_health.v0.1",
        "project_id": project.get("project_id"),
        "overall": overall,
        "release_ready": release_ready,
        "hard_blockers": sorted(set(hard_blockers)),
        "dimensions": dimensions,
        "release_prerequisites": release_prerequisites,
        "rule": "NO AGGREGATE SCORE MAY HIDE A HARD BLOCKER",
    }
