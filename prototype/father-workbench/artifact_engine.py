"""Stage artifact/document state rules for FATHER."""

from __future__ import annotations

from typing import Any

ALLOWED_STATUSES = {
    "DRAFT",
    "IN_REVIEW",
    "PASS",
    "FAIL",
    "BLOCKED",
    "TBD",
}
ACCEPTED_STATUSES = {"PASS", "APPROVED", "FINAL"}


def find_stage(
    state: dict[str, Any],
    stage_id: str,
) -> dict[str, Any] | None:
    for stage in state.get("stages", []):
        if stage.get("id") == stage_id:
            return stage
    return None


def find_artifact(
    stage: dict[str, Any],
    artifact_id: str,
) -> dict[str, Any] | None:
    for item in (stage.get("documents") or {}).get("items", []):
        if item.get("id") == artifact_id:
            return item
    return None


def list_artifacts(state: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for stage in state.get("stages", []):
        for artifact in (stage.get("documents") or {}).get("items", []):
            result.append(
                {
                    "stage_id": stage.get("id"),
                    "stage_name": stage.get("name"),
                    **artifact,
                }
            )
    return result


def validate_artifact_update(
    *,
    state: dict[str, Any],
    stage_id: str,
    artifact_id: str,
    title: str,
    status: str,
    rationale: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    errors: list[str] = []
    stage = find_stage(state, stage_id)
    if not stage:
        errors.append("STAGE_NOT_FOUND")

    artifact_id = artifact_id.strip()
    title = title.strip()
    status = status.upper().strip()

    if not artifact_id:
        errors.append("ARTIFACT_ID_REQUIRED")
    if not title:
        errors.append("ARTIFACT_TITLE_REQUIRED")
    if status not in ALLOWED_STATUSES:
        errors.append("INVALID_ARTIFACT_STATUS")
    if not rationale.strip():
        errors.append("RATIONALE_REQUIRED")
    if status == "PASS" and not evidence_refs:
        errors.append("EVIDENCE_REFS_REQUIRED_FOR_PASS")

    return {
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "stage_id": stage_id,
        "artifact_id": artifact_id,
        "title": title,
        "status": status,
    }


def apply_artifact_update(
    *,
    state: dict[str, Any],
    stage_id: str,
    artifact_id: str,
    title: str,
    status: str,
    rationale: str,
    evidence_refs: list[str],
    decided_by: str,
    source_ref: str | None = None,
) -> dict[str, Any]:
    validation = validate_artifact_update(
        state=state,
        stage_id=stage_id,
        artifact_id=artifact_id,
        title=title,
        status=status,
        rationale=rationale,
        evidence_refs=evidence_refs,
    )
    if not validation["valid"]:
        raise ValueError(",".join(validation["errors"]))

    stage = find_stage(state, stage_id)
    assert stage is not None
    documents = stage.setdefault(
        "documents",
        {"done": 0, "total": 0, "items": []},
    )
    items = documents.setdefault("items", [])
    artifact = find_artifact(stage, artifact_id)

    previous_status = artifact.get("status") if artifact else None
    if artifact is None:
        artifact = {
            "id": artifact_id.strip(),
            "title": title.strip(),
            "status": status.upper().strip(),
        }
        items.append(artifact)
    else:
        artifact["title"] = title.strip()
        artifact["status"] = status.upper().strip()

    if source_ref:
        artifact["source_ref"] = source_ref.strip()

    artifact.setdefault("status_history", []).append(
        {
            "from": previous_status,
            "to": status.upper().strip(),
            "rationale": rationale.strip(),
            "evidence_refs": list(evidence_refs),
            "decided_by": decided_by.strip() or "HUMAN",
        }
    )

    accepted_count = sum(
        1 for item in items
        if item.get("status") in ACCEPTED_STATUSES
    )
    documents["done"] = accepted_count
    documents["total"] = max(
        int(documents.get("total") or 0),
        len(items),
    )

    return {
        "state": state,
        "artifact": artifact,
        "previous_status": previous_status,
        "accepted_count": accepted_count,
        "document_total": documents["total"],
    }
