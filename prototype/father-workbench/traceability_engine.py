"""Build a project traceability graph from FATHER runtime and project state."""

from __future__ import annotations

from typing import Any


def build_traceability_graph(
    *,
    project: dict[str, Any],
    state: dict[str, Any],
    evidence: list[dict[str, Any]],
    events: list[dict[str, Any]],
    live: dict[str, Any] | None = None,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    unresolved: set[str] = set()

    def add_node(node_id: str, kind: str, **attrs: Any) -> None:
        nodes.setdefault(
            node_id,
            {"id": node_id, "kind": kind, **attrs},
        )

    def edge(source: str, relation: str, target: str) -> None:
        edges.append(
            {
                "source": source,
                "relation": relation,
                "target": target,
            }
        )

    project_id = str(project.get("project_id"))
    project_node = f"project:{project_id}"
    add_node(
        project_node,
        "PROJECT",
        label=project.get("name") or project_id,
        status=project.get("status"),
    )

    evidence_ids = {
        str(item.get("evidence_id"))
        for item in evidence
        if item.get("evidence_id")
    }
    for item in evidence:
        evidence_id = str(item.get("evidence_id") or "")
        if not evidence_id:
            continue
        node_id = f"evidence:{evidence_id}"
        add_node(
            node_id,
            "EVIDENCE",
            label=evidence_id,
            evidence_type=item.get("evidence_type"),
            captured_at=item.get("captured_at"),
            payload_sha256=item.get("payload_sha256"),
        )
        edge(project_node, "HAS_EVIDENCE", node_id)

    for stage in state.get("stages", []):
        stage_id = str(stage.get("id"))
        stage_node = f"stage:{stage_id}"
        add_node(
            stage_node,
            "STAGE",
            label=stage.get("name") or stage_id,
            status=stage.get("status"),
            gate=stage.get("gate"),
        )
        edge(project_node, "HAS_STAGE", stage_node)

        gate_node = f"gate:{stage_id}"
        add_node(
            gate_node,
            "GATE",
            label=f"{stage_id} Gate",
            status=stage.get("gate"),
        )
        edge(stage_node, "HAS_GATE", gate_node)

        for decision_index, decision in enumerate(
            stage.get("gate_decisions") or [],
            start=1,
        ):
            decision_node = f"gate-decision:{stage_id}:{decision_index}"
            add_node(
                decision_node,
                "GATE_DECISION",
                label=decision.get("decision"),
                rationale=decision.get("rationale"),
                decided_by=decision.get("decided_by"),
            )
            edge(gate_node, "DECIDED_BY", decision_node)
            for ref in decision.get("evidence_refs") or []:
                ref = str(ref)
                target = f"evidence:{ref}"
                if ref not in evidence_ids:
                    unresolved.add(ref)
                    add_node(
                        target,
                        "UNRESOLVED_EVIDENCE_REF",
                        label=ref,
                    )
                edge(decision_node, "SUPPORTED_BY", target)

        for analysis in stage.get("specialist_analyses") or []:
            analysis_id = str(analysis.get("analysis_id") or "")
            if not analysis_id:
                continue
            node_id = f"analysis:{stage_id}:{analysis_id}"
            add_node(
                node_id,
                "SPECIALIST_ANALYSIS",
                label=analysis.get("title") or analysis_id,
                role=analysis.get("role"),
                status=analysis.get("status"),
            )
            edge(stage_node, "HAS_ANALYSIS", node_id)
            for ref in analysis.get("evidence_refs") or []:
                ref = str(ref)
                target = f"evidence:{ref}"
                if ref not in evidence_ids:
                    unresolved.add(ref)
                    add_node(
                        target,
                        "UNRESOLVED_EVIDENCE_REF",
                        label=ref,
                    )
                edge(node_id, "SUPPORTED_BY", target)

        for decision in stage.get("decision_records") or []:
            decision_id = str(decision.get("decision_id") or "")
            if not decision_id:
                continue
            node_id = f"decision:{stage_id}:{decision_id}"
            add_node(
                node_id,
                "DECISION",
                label=decision.get("title") or decision_id,
                status=decision.get("status"),
                owner=decision.get("owner"),
            )
            edge(stage_node, "HAS_DECISION", node_id)
            for ref in decision.get("evidence_refs") or []:
                ref = str(ref)
                target = f"evidence:{ref}"
                if ref not in evidence_ids:
                    unresolved.add(ref)
                    add_node(
                        target,
                        "UNRESOLVED_EVIDENCE_REF",
                        label=ref,
                    )
                edge(node_id, "SUPPORTED_BY", target)

        for risk in stage.get("risk_records") or []:
            risk_id = str(risk.get("risk_id") or "")
            if not risk_id:
                continue
            node_id = f"risk:{stage_id}:{risk_id}"
            add_node(
                node_id,
                "RISK",
                label=risk.get("title") or risk_id,
                status=risk.get("status"),
                likelihood=risk.get("likelihood"),
                impact=risk.get("impact"),
                owner=risk.get("owner"),
            )
            edge(stage_node, "HAS_RISK", node_id)
            for ref in risk.get("evidence_refs") or []:
                ref = str(ref)
                target = f"evidence:{ref}"
                if ref not in evidence_ids:
                    unresolved.add(ref)
                    add_node(
                        target,
                        "UNRESOLVED_EVIDENCE_REF",
                        label=ref,
                    )
                edge(node_id, "SUPPORTED_BY", target)

        for artifact in (stage.get("documents") or {}).get("items", []):
            artifact_id = str(artifact.get("id"))
            artifact_node = f"artifact:{stage_id}:{artifact_id}"
            add_node(
                artifact_node,
                "ARTIFACT",
                label=artifact.get("title") or artifact_id,
                artifact_id=artifact_id,
                status=artifact.get("status"),
                source_ref=artifact.get("source_ref"),
            )
            edge(stage_node, "HAS_ARTIFACT", artifact_node)

            for history_index, history in enumerate(
                artifact.get("status_history") or [],
                start=1,
            ):
                decision_node = (
                    f"artifact-decision:{stage_id}:{artifact_id}:{history_index}"
                )
                add_node(
                    decision_node,
                    "ARTIFACT_DECISION",
                    label=f"{history.get('from')}→{history.get('to')}",
                    rationale=history.get("rationale"),
                    decided_by=history.get("decided_by"),
                )
                edge(artifact_node, "STATUS_DECIDED_BY", decision_node)
                for ref in history.get("evidence_refs") or []:
                    ref = str(ref)
                    target = f"evidence:{ref}"
                    if ref not in evidence_ids:
                        unresolved.add(ref)
                        add_node(
                            target,
                            "UNRESOLVED_EVIDENCE_REF",
                            label=ref,
                        )
                    edge(decision_node, "SUPPORTED_BY", target)

    for event in events[:200]:
        event_id = str(event.get("event_id") or "")
        if not event_id:
            continue
        event_node = f"event:{event_id}"
        add_node(
            event_node,
            "MANUFACTURING_EVENT",
            label=event.get("event_type") or event_id,
            occurred_at=event.get("occurred_at"),
            source_ref=event.get("source_ref"),
        )
        edge(project_node, "HAS_EVENT", event_node)

        source_ref = str(event.get("source_ref") or "")
        if source_ref in evidence_ids:
            edge(event_node, "EVIDENCED_BY", f"evidence:{source_ref}")

    if live:
        provider = str(live.get("provider") or "unknown")
        repository = str(
            (live.get("repository") or {}).get("full_name")
            or project.get("repository")
            or "unknown"
        )
        branch = str(
            (live.get("branch") or {}).get("name")
            or project.get("branch")
            or "unknown"
        )
        head_sha = (live.get("branch") or {}).get("head_sha")
        provider_node = f"provider:{provider}"
        repo_node = f"repository:{provider}:{repository}"
        branch_node = f"branch:{provider}:{repository}:{branch}"
        add_node(provider_node, "PROVIDER", label=provider)
        add_node(repo_node, "REPOSITORY", label=repository)
        add_node(
            branch_node,
            "BRANCH",
            label=branch,
            head_sha=head_sha,
        )
        edge(project_node, "USES_PROVIDER", provider_node)
        edge(provider_node, "HOSTS", repo_node)
        edge(repo_node, "HAS_BRANCH", branch_node)

        if head_sha:
            commit_node = f"commit:{provider}:{head_sha}"
            add_node(
                commit_node,
                "COMMIT",
                label=str(head_sha)[:12],
                sha=head_sha,
            )
            edge(branch_node, "POINTS_TO", commit_node)

        for run in live.get("workflow_runs") or []:
            run_id = str(run.get("id") or "")
            if not run_id:
                continue
            run_node = f"workflow:{provider}:{run_id}"
            add_node(
                run_node,
                "WORKFLOW_RUN",
                label=run.get("name") or run_id,
                status=run.get("status"),
                conclusion=run.get("conclusion"),
                head_sha=run.get("head_sha"),
            )
            edge(repo_node, "HAS_WORKFLOW_RUN", run_node)
            if head_sha and run.get("head_sha") == head_sha:
                edge(run_node, "VALIDATES", f"commit:{provider}:{head_sha}")

        for artifact in live.get("artifacts") or []:
            artifact_id = str(artifact.get("id") or "")
            if not artifact_id:
                continue
            ci_artifact_node = f"ci-artifact:{provider}:{artifact_id}"
            add_node(
                ci_artifact_node,
                "CI_ARTIFACT",
                label=artifact.get("name") or artifact_id,
                digest=artifact.get("digest"),
                expired=artifact.get("expired"),
            )
            edge(repo_node, "HAS_CI_ARTIFACT", ci_artifact_node)
            run_id = artifact.get("workflow_run_id")
            if run_id:
                edge(
                    f"workflow:{provider}:{run_id}",
                    "PRODUCED",
                    ci_artifact_node,
                )

    return {
        "schema_version": "father.traceability_graph.v0.1",
        "project_id": project_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "unresolved_evidence_refs": sorted(unresolved),
        "integrity_status": "PASS" if not unresolved else "PARTIAL",
        "nodes": list(nodes.values()),
        "edges": edges,
    }
