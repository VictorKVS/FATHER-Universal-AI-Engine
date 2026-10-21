"""Conservative stage gate evaluation and decision rules for FATHER."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def state_etag(state: dict[str, Any]) -> str:
    payload = json.dumps(
        state,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def stage_from_state(
    state: dict[str, Any],
    stage_id: str,
) -> dict[str, Any] | None:
    for stage in state.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    return None


def evaluate_stage_gate(
    state: dict[str, Any],
    stage_id: str,
    policies: dict[str, Any],
) -> dict[str, Any]:
    stage = stage_from_state(state, stage_id)
    if not stage:
        return {
            "stage_id": stage_id,
            "mechanical_status": "BLOCKED",
            "blockers": ["STAGE_NOT_FOUND"],
            "missing_documents": [],
            "nonaccepted_documents": [],
            "can_auto_pass": False,
            "review_candidate": False,
        }

    policy = (policies.get("stages") or {}).get(stage_id)
    if not policy:
        return {
            "stage_id": stage_id,
            "current_gate": stage.get("gate"),
            "mechanical_status": "BLOCKED",
            "blockers": ["GATE_POLICY_NOT_DEFINED"],
            "missing_documents": [],
            "nonaccepted_documents": [],
            "can_auto_pass": False,
            "review_candidate": False,
        }

    accepted = set(policies.get("accepted_document_statuses") or [])
    required = list(policy.get("required_documents") or [])
    docs = {
        str(item.get("id")): item
        for item in (stage.get("documents") or {}).get("items", [])
    }

    missing = [doc_id for doc_id in required if doc_id not in docs]
    nonaccepted = [
        {
            "id": doc_id,
            "status": docs[doc_id].get("status"),
        }
        for doc_id in required
        if doc_id in docs and docs[doc_id].get("status") not in accepted
    ]

    blockers: list[str] = []
    if missing:
        blockers.append("REQUIRED_DOCUMENTS_MISSING")
    if nonaccepted:
        blockers.append("REQUIRED_DOCUMENTS_NOT_ACCEPTED")
    if stage.get("status") == "BLOCKED":
        blockers.append("STAGE_STATUS_BLOCKED")

    complete = not blockers
    return {
        "stage_id": stage_id,
        "current_stage_status": stage.get("status"),
        "current_gate": stage.get("gate"),
        "mechanical_status": "COMPLETE" if complete else "INCOMPLETE",
        "blockers": blockers,
        "missing_documents": missing,
        "nonaccepted_documents": nonaccepted,
        "required_document_count": len(required),
        "accepted_required_document_count": (
            len(required) - len(missing) - len(nonaccepted)
        ),
        "can_auto_pass": False,
        "review_candidate": complete,
        "recommended_action": (
            "READY_FOR_HUMAN_REVIEW" if complete else "CONTINUE_STAGE_WORK"
        ),
        "state_etag": state_etag(state),
    }


def validate_gate_decision(
    state: dict[str, Any],
    stage_id: str,
    decision: str,
    rationale: str,
    evidence_refs: list[str],
    policies: dict[str, Any],
) -> dict[str, Any]:
    decision = decision.upper().strip()
    allowed = {"PASS", "FAIL", "HOLD", "RETURN"}
    errors: list[str] = []

    if decision not in allowed:
        errors.append("INVALID_GATE_DECISION")

    evaluation = evaluate_stage_gate(state, stage_id, policies)
    if evaluation.get("mechanical_status") == "BLOCKED":
        errors.extend(evaluation.get("blockers") or [])

    if not rationale.strip():
        errors.append("RATIONALE_REQUIRED")

    if decision == "PASS":
        if not evaluation.get("review_candidate"):
            errors.append("MECHANICAL_GATE_NOT_COMPLETE")
        if not evidence_refs:
            errors.append("EVIDENCE_REFS_REQUIRED")
        stage = stage_from_state(state, stage_id)
        if stage and stage.get("status") == "BLOCKED":
            errors.append("BLOCKED_STAGE_CANNOT_PASS")

    # preserve order but remove duplicates
    errors = list(dict.fromkeys(errors))
    return {
        "valid": not errors,
        "decision": decision,
        "errors": errors,
        "evaluation": evaluation,
    }


def apply_gate_decision(
    state: dict[str, Any],
    stage_id: str,
    decision: str,
    rationale: str,
    evidence_refs: list[str],
    decided_by: str,
    policies: dict[str, Any],
) -> dict[str, Any]:
    validation = validate_gate_decision(
        state,
        stage_id,
        decision,
        rationale,
        evidence_refs,
        policies,
    )
    if not validation["valid"]:
        raise ValueError(",".join(validation["errors"]))

    stage = stage_from_state(state, stage_id)
    if stage is None:
        raise ValueError("STAGE_NOT_FOUND")

    decision = decision.upper().strip()
    gate_value = {
        "PASS": "PASS",
        "FAIL": "FAIL",
        "HOLD": "HOLD",
        "RETURN": "RETURN",
    }[decision]

    stage["gate"] = gate_value
    if decision == "PASS":
        stage["status"] = "PASS"
    elif decision == "FAIL":
        stage["status"] = "FAIL"
    elif decision == "HOLD":
        stage["status"] = "HOLD"
    elif decision == "RETURN":
        stage["status"] = "IN_PROGRESS"

    stage.setdefault("gate_decisions", []).append(
        {
            "decision": decision,
            "rationale": rationale.strip(),
            "evidence_refs": list(evidence_refs),
            "decided_by": decided_by.strip() or "HUMAN",
        }
    )
    return state
