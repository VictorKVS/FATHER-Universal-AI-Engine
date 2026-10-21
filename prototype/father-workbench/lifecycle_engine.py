"""Project stage eligibility and current-stage derivation for FATHER."""

from __future__ import annotations

from typing import Any


def _stage_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(stage.get("id")): stage
        for stage in state.get("stages", [])
        if stage.get("id")
    }


def _gate_passed(stage: dict[str, Any] | None) -> bool:
    return bool(stage and stage.get("gate") == "PASS")


def reconcile_project_flow(
    state: dict[str, Any],
    flow: dict[str, Any],
) -> dict[str, Any]:
    stages = _stage_map(state)
    changes: list[dict[str, Any]] = []
    ordered = list(flow.get("stages") or [])

    eligibility: dict[str, bool] = {}
    for rule in ordered:
        stage_id = str(rule.get("id"))
        requirements = list(rule.get("requires") or [])
        eligibility[stage_id] = all(
            _gate_passed(stages.get(required))
            for required in requirements
        )

    current_stage: str | None = None
    for rule in ordered:
        stage_id = str(rule.get("id"))
        stage = stages.get(stage_id)
        if not stage:
            continue
        if _gate_passed(stage):
            if stage.get("status") != "PASS":
                changes.append(
                    {
                        "stage_id": stage_id,
                        "from": stage.get("status"),
                        "to": "PASS",
                        "reason": "GATE_PASS",
                    }
                )
                stage["status"] = "PASS"
            continue

        if eligibility.get(stage_id):
            if current_stage is None:
                current_stage = stage_id
            if stage.get("status") in {
                "BLOCKED",
                "NOT_STARTED",
                "WAITING",
            }:
                changes.append(
                    {
                        "stage_id": stage_id,
                        "from": stage.get("status"),
                        "to": "READY",
                        "reason": "DEPENDENCIES_PASSED",
                    }
                )
                stage["status"] = "READY"

    previous_current = state.get("current_stage")
    if current_stage and previous_current != current_stage:
        state["current_stage"] = current_stage

    return {
        "state": state,
        "current_stage": state.get("current_stage"),
        "previous_current_stage": previous_current,
        "eligibility": eligibility,
        "changes": changes,
    }
