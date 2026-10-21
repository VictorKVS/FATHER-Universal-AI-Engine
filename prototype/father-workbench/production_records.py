"""Structured specialist analyses, decisions and risks for FATHER stages."""

from __future__ import annotations

from typing import Any

ANALYSIS_STATUSES = {"DRAFT", "IN_REVIEW", "VERIFIED", "REJECTED"}
DECISION_STATUSES = {"PROPOSED", "APPROVED", "REJECTED", "SUPERSEDED"}
RISK_STATUSES = {"OPEN", "MITIGATING", "ACCEPTED", "CLOSED"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _stage(state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    for stage in state.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    raise ValueError("STAGE_NOT_FOUND")


def upsert_specialist_analysis(
    *,
    state: dict[str, Any],
    stage_id: str,
    analysis_id: str,
    role: str,
    title: str,
    summary: str,
    status: str,
    findings: list[str],
    recommendations: list[str],
    evidence_refs: list[str],
    author: str,
) -> dict[str, Any]:
    status = status.upper().strip()
    if status not in ANALYSIS_STATUSES:
        raise ValueError("INVALID_ANALYSIS_STATUS")
    if not analysis_id.strip() or not role.strip() or not title.strip():
        raise ValueError("ANALYSIS_ID_ROLE_TITLE_REQUIRED")
    if not summary.strip():
        raise ValueError("ANALYSIS_SUMMARY_REQUIRED")
    if status == "VERIFIED" and not evidence_refs:
        raise ValueError("VERIFIED_ANALYSIS_REQUIRES_EVIDENCE")

    stage = _stage(state, stage_id)
    records = stage.setdefault("specialist_analyses", [])
    record = next(
        (item for item in records if item.get("analysis_id") == analysis_id),
        None,
    )
    previous_status = record.get("status") if record else None
    payload = {
        "analysis_id": analysis_id.strip(),
        "role": role.strip(),
        "title": title.strip(),
        "summary": summary.strip(),
        "status": status,
        "findings": [str(item).strip() for item in findings if str(item).strip()],
        "recommendations": [
            str(item).strip()
            for item in recommendations
            if str(item).strip()
        ],
        "evidence_refs": [
            str(item).strip()
            for item in evidence_refs
            if str(item).strip()
        ],
        "author": author.strip() or role.strip(),
    }
    if record is None:
        record = payload
        records.append(record)
    else:
        record.update(payload)
    record.setdefault("status_history", []).append(
        {
            "from": previous_status,
            "to": status,
            "author": author.strip() or role.strip(),
            "evidence_refs": payload["evidence_refs"],
        }
    )
    return {
        "state": state,
        "record": record,
        "previous_status": previous_status,
    }


def upsert_decision_record(
    *,
    state: dict[str, Any],
    stage_id: str,
    decision_id: str,
    title: str,
    context: str,
    decision: str,
    rationale: str,
    alternatives: list[str],
    rejected_reasons: list[str],
    constraints: list[str],
    evidence_refs: list[str],
    owner: str,
    status: str,
    revisit_triggers: list[str],
) -> dict[str, Any]:
    status = status.upper().strip()
    if status not in DECISION_STATUSES:
        raise ValueError("INVALID_DECISION_STATUS")
    if not decision_id.strip() or not title.strip() or not decision.strip():
        raise ValueError("DECISION_ID_TITLE_VALUE_REQUIRED")
    if not context.strip() or not rationale.strip() or not owner.strip():
        raise ValueError("DECISION_CONTEXT_RATIONALE_OWNER_REQUIRED")
    if status == "APPROVED" and not evidence_refs:
        raise ValueError("APPROVED_DECISION_REQUIRES_EVIDENCE")

    stage = _stage(state, stage_id)
    records = stage.setdefault("decision_records", [])
    record = next(
        (item for item in records if item.get("decision_id") == decision_id),
        None,
    )
    previous_status = record.get("status") if record else None
    payload = {
        "decision_id": decision_id.strip(),
        "title": title.strip(),
        "context": context.strip(),
        "decision": decision.strip(),
        "rationale": rationale.strip(),
        "alternatives": [
            str(item).strip() for item in alternatives if str(item).strip()
        ],
        "rejected_reasons": [
            str(item).strip()
            for item in rejected_reasons
            if str(item).strip()
        ],
        "constraints": [
            str(item).strip() for item in constraints if str(item).strip()
        ],
        "evidence_refs": [
            str(item).strip()
            for item in evidence_refs
            if str(item).strip()
        ],
        "owner": owner.strip(),
        "status": status,
        "revisit_triggers": [
            str(item).strip()
            for item in revisit_triggers
            if str(item).strip()
        ],
    }
    if record is None:
        record = payload
        records.append(record)
    else:
        record.update(payload)
    record.setdefault("status_history", []).append(
        {
            "from": previous_status,
            "to": status,
            "owner": owner.strip(),
            "evidence_refs": payload["evidence_refs"],
        }
    )
    quality_warnings: list[str] = []
    if status == "APPROVED" and not payload["alternatives"]:
        quality_warnings.append("NO_ALTERNATIVES_RECORDED")
    if status == "APPROVED" and not payload["revisit_triggers"]:
        quality_warnings.append("NO_REVISIT_TRIGGERS_RECORDED")
    return {
        "state": state,
        "record": record,
        "previous_status": previous_status,
        "quality_warnings": quality_warnings,
    }


def upsert_risk_record(
    *,
    state: dict[str, Any],
    stage_id: str,
    risk_id: str,
    title: str,
    description: str,
    likelihood: str,
    impact: str,
    treatment: str,
    owner: str,
    status: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    likelihood = likelihood.upper().strip()
    impact = impact.upper().strip()
    status = status.upper().strip()
    if likelihood not in RISK_LEVELS or impact not in RISK_LEVELS:
        raise ValueError("INVALID_RISK_LEVEL")
    if status not in RISK_STATUSES:
        raise ValueError("INVALID_RISK_STATUS")
    if (
        not risk_id.strip()
        or not title.strip()
        or not description.strip()
        or not owner.strip()
    ):
        raise ValueError("RISK_REQUIRED_FIELDS_MISSING")
    if status in {"ACCEPTED", "CLOSED"} and not evidence_refs:
        raise ValueError("RISK_TERMINAL_STATUS_REQUIRES_EVIDENCE")

    stage = _stage(state, stage_id)
    records = stage.setdefault("risk_records", [])
    record = next(
        (item for item in records if item.get("risk_id") == risk_id),
        None,
    )
    previous_status = record.get("status") if record else None
    payload = {
        "risk_id": risk_id.strip(),
        "title": title.strip(),
        "description": description.strip(),
        "likelihood": likelihood,
        "impact": impact,
        "treatment": treatment.strip(),
        "owner": owner.strip(),
        "status": status,
        "evidence_refs": [
            str(item).strip()
            for item in evidence_refs
            if str(item).strip()
        ],
    }
    if record is None:
        record = payload
        records.append(record)
    else:
        record.update(payload)
    record.setdefault("status_history", []).append(
        {
            "from": previous_status,
            "to": status,
            "owner": owner.strip(),
            "evidence_refs": payload["evidence_refs"],
        }
    )
    return {
        "state": state,
        "record": record,
        "previous_status": previous_status,
    }
