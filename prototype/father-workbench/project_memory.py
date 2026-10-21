"""Source-grounded Project Memory draft builder."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _uniq(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def collect_decisions(state: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for stage in state.get("stages", []):
        stage_id = str(stage.get("id") or "")
        for item in stage.get("decision_records", []):
            if str(item.get("status") or "").upper() != "APPROVED":
                continue
            records.append({**item, "stage_id": stage_id})
    return records


def collect_lessons(state: dict[str, Any]) -> list[str]:
    lessons: list[str] = []
    for stage in state.get("stages", []):
        lessons.extend(
            str(item).strip()
            for item in stage.get("lessons", [])
            if str(item).strip()
        )
    return _uniq(lessons)


def collect_security_result(state: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for stage in state.get("stages", []):
        stage_id = str(stage.get("id") or "")
        if stage_id not in {"PD-02", "DS-02"}:
            continue
        analysis = str(stage.get("analysis") or "").strip()
        if analysis:
            result.append(f"{stage_id}: {analysis}")
        for decision in stage.get("decision_records", []):
            if str(decision.get("status") or "").upper() == "APPROVED":
                text = str(decision.get("decision") or "").strip()
                if text:
                    result.append(f"{stage_id}: {text}")
    return _uniq(result)


def project_memory_readiness(
    health: dict[str, Any],
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    if health.get("release_ready") is not True:
        blockers.append("PROJECT_NOT_RELEASE_READY")
    if not evidence_records:
        blockers.append("NO_PROJECT_EVIDENCE")
    return {
        "ready_for_draft": not blockers,
        "blockers": blockers,
    }


def build_project_memory(
    *,
    project: dict[str, Any],
    state: dict[str, Any],
    health: dict[str, Any],
    evidence_records: list[dict[str, Any]],
    source_state_etag: str,
) -> dict[str, Any]:
    readiness = project_memory_readiness(health, evidence_records)
    decisions = collect_decisions(state)
    lessons = collect_lessons(state)

    rationales = _uniq(
        [str(item.get("rationale") or "") for item in decisions]
    )
    constraints = _uniq(
        [
            str(value)
            for item in decisions
            for value in item.get("constraints", [])
        ]
    )
    revisit = _uniq(
        [
            str(value)
            for item in decisions
            for value in item.get("revisit_triggers", [])
        ]
    )
    decision_evidence = _uniq(
        [
            str(value)
            for item in decisions
            for value in item.get("evidence_refs", [])
        ]
    )

    rejected: list[dict[str, str]] = []
    for item in decisions:
        alternatives = list(item.get("alternatives") or [])
        reasons = list(item.get("rejected_reasons") or [])
        triggers = list(item.get("revisit_triggers") or [])
        for index, alternative in enumerate(alternatives):
            rejected.append(
                {
                    "decision_id": str(item.get("decision_id") or ""),
                    "alternative": str(alternative),
                    "why_rejected": str(
                        reasons[index] if index < len(reasons) else "TBD"
                    ),
                    "revisit_trigger": str(
                        triggers[0] if triggers else "TBD"
                    ),
                }
            )

    evidence_ids = _uniq(
        decision_evidence
        + [
            str(item.get("evidence_id") or "")
            for item in evidence_records[-50:]
        ]
    )

    manufactured = project.get("manufactured_objects") or []
    what_built = (
        "; ".join(
            str(item) for item in manufactured if str(item).strip()
        )
        or str(state.get("description") or "").strip()
        or "TBD"
    )
    why_needed = (
        str(project.get("description") or "").strip()
        or str(state.get("description") or "").strip()
        or "TBD"
    )
    final_solution = _uniq(
        [str(item.get("decision") or "") for item in decisions]
    )

    status = "DRAFT" if readiness["ready_for_draft"] else "NOT_READY"

    return {
        "schema_version": "father.project_memory.v0.1",
        "artifact": "PROJECT_MEMORY",
        "project_id": project.get("project_id"),
        "project_name": project.get("name"),
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_state_etag": source_state_etag,
        "source_health_overall": health.get("overall"),
        "readiness": readiness,
        "sections": {
            "what_was_built": what_built,
            "why_it_was_needed": why_needed,
            "final_solution": final_solution or ["TBD"],
            "why_this_solution": rationales or ["TBD"],
            "rejected_alternatives": rejected,
            "key_constraints": constraints or ["TBD"],
            "tradeoffs": ["TBD"],
            "security_compliance_result": (
                collect_security_result(state) or ["TBD"]
            ),
            "cost_result": (
                project.get("budget_summary")
                if project.get("budget_summary")
                else "TBD"
            ),
            "known_limitations": ["TBD"],
            "lessons_learned": lessons or ["TBD"],
            "revisit_triggers": revisit or ["TBD"],
            "key_evidence": evidence_ids,
        },
        "decision_refs": [
            {
                "decision_id": item.get("decision_id"),
                "stage_id": item.get("stage_id"),
                "title": item.get("title"),
                "evidence_refs": item.get("evidence_refs", []),
            }
            for item in decisions
        ],
        "rules": {
            "generated_summary_is_not_primary_source": True,
            "approval_requires_review": True,
            "approved_memory_requires_evidence_links": True,
            "material_change_requires_new_memory_version": True,
        },
    }


def render_project_memory_markdown(memory: dict[str, Any]) -> str:
    sections = memory.get("sections") or {}

    def lines(value: Any) -> str:
        if isinstance(value, list):
            if not value:
                return "- None recorded"
            if isinstance(value[0], dict):
                return "\n".join(
                    "- "
                    + " | ".join(
                        f"{key}: {item.get(key, '')}"
                        for key in item
                    )
                    for item in value
                )
            return "\n".join(f"- {item}" for item in value)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value or "TBD")

    return f"""# PROJECT MEMORY

**Project ID:** {memory.get('project_id')}
**Project:** {memory.get('project_name')}
**Status:** {memory.get('status')}
**Generated:** {memory.get('generated_at')}
**Source state ETag:** {memory.get('source_state_etag')}

## 1. What was built
{lines(sections.get('what_was_built'))}

## 2. Why it was needed
{lines(sections.get('why_it_was_needed'))}

## 3. Final solution
{lines(sections.get('final_solution'))}

## 4. Why this solution
{lines(sections.get('why_this_solution'))}

## 5. Rejected alternatives
{lines(sections.get('rejected_alternatives'))}

## 6. Key constraints
{lines(sections.get('key_constraints'))}

## 7. Important trade-offs
{lines(sections.get('tradeoffs'))}

## 8. Security / Compliance result
{lines(sections.get('security_compliance_result'))}

## 9. Cost result
{lines(sections.get('cost_result'))}

## 10. Known limitations
{lines(sections.get('known_limitations'))}

## 11. Lessons learned
{lines(sections.get('lessons_learned'))}

## 12. Revisit triggers
{lines(sections.get('revisit_triggers'))}

## 13. Key evidence
{lines(sections.get('key_evidence'))}

---
Generated by FATHER from tracked project records. This summary does not replace original evidence.
"""
