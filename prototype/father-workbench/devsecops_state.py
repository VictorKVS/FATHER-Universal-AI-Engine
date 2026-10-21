"""Commit-bound DevSecOps evidence evaluation."""

from __future__ import annotations

from typing import Any


def evaluate_devsecops_state(live: dict[str, Any] | None) -> dict[str, Any]:
    if not live:
        return {
            "status": "UNKNOWN",
            "head_sha": None,
            "ci_current_head": "UNKNOWN",
            "evidence_artifact": "UNKNOWN",
            "blockers": ["LIVE_PROVIDER_STATE_UNAVAILABLE"],
        }

    head_sha = (live.get("branch") or {}).get("head_sha")
    if not head_sha:
        return {
            "status": "BLOCKED",
            "head_sha": None,
            "ci_current_head": "UNKNOWN",
            "evidence_artifact": "UNKNOWN",
            "blockers": ["HEAD_SHA_UNAVAILABLE"],
        }

    runs = live.get("workflow_runs") or []
    run = next(
        (
            item for item in runs
            if item.get("head_sha") == head_sha
        ),
        None,
    )

    blockers: list[str] = []
    if not run:
        ci_state = "NOT_RUN"
        blockers.append("CURRENT_HEAD_WORKFLOW_NOT_FOUND")
    elif run.get("status") != "completed":
        ci_state = "RUNNING"
        blockers.append("CURRENT_HEAD_WORKFLOW_NOT_COMPLETE")
    elif run.get("conclusion") == "success":
        ci_state = "PASS"
    else:
        ci_state = "FAIL"
        blockers.append("CURRENT_HEAD_WORKFLOW_NOT_SUCCESS")

    artifacts = live.get("artifacts") or []
    expected_names = {
        f"father-devsecops-{head_sha}",
        f"father-devsecops-{head_sha[:40]}",
    }
    artifact = next(
        (
            item for item in artifacts
            if item.get("name") in expected_names
            and item.get("expired") is not True
            and (
                not run
                or not item.get("workflow_run_id")
                or item.get("workflow_run_id") == run.get("id")
            )
        ),
        None,
    )
    if artifact:
        artifact_state = "PRESENT"
    else:
        artifact_state = "MISSING"
        blockers.append("CURRENT_HEAD_DEVSECOPS_ARTIFACT_MISSING")

    status = (
        "PASS"
        if ci_state == "PASS" and artifact_state == "PRESENT"
        else "BLOCKED"
    )
    return {
        "status": status,
        "head_sha": head_sha,
        "ci_current_head": ci_state,
        "workflow_run": run,
        "evidence_artifact": artifact_state,
        "artifact": artifact,
        "blockers": blockers,
        "rule": "CURRENT_HEAD_CI_PASS_AND_COMMIT_BOUND_ARTIFACT_REQUIRED",
    }
