"""Multi-model cells built on the same UniversalProcessor contract."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from father_core.adapters.registry import adapter_for
from father_core.contracts import MessageEnvelope, RunResult, utc_now
from father_core.processor import UniversalProcessor
from father_core.zoo import Zoo


@dataclass(frozen=True)
class RoutedRunResult:
    schema_version: str
    execution_id: str
    cell_id: str
    routing_mode: str
    status: str
    started_at: str
    finished_at: str
    selected_model_id: str | None
    output: MessageEnvelope | None
    attempts: list[RunResult]
    routing_evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RoutedFactoryCell:
    SUPPORTED_MODES = {"PRIMARY_FALLBACK"}

    def __init__(
        self,
        *,
        repo_root: Path,
        cell_id: str,
        test_mode: bool = False,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.zoo = Zoo(self.repo_root)
        self.cell_spec = self.zoo.cell(cell_id)
        self.agent_spec = self.zoo.agent(
            str(self.cell_spec["agent_id"])
        )
        self.routing_mode = str(self.cell_spec.get("mode") or "")
        if self.routing_mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"ROUTING_MODE_NOT_SUPPORTED:{self.routing_mode}"
            )
        key = "test_model_ids" if test_mode else "model_ids"
        model_ids = self.cell_spec.get(key) or []
        if not isinstance(model_ids, list) or len(model_ids) < 2:
            raise ValueError("MULTI_MODEL_CELL_REQUIRES_TWO_MODELS")
        self.model_specs = [
            self.zoo.model(str(model_id))
            for model_id in model_ids
        ]

    def run(self, value: Any) -> RoutedRunResult:
        execution_id = f"EXEC-{uuid.uuid4().hex[:16].upper()}"
        started_at = utc_now()
        attempts: list[RunResult] = []
        selected: RunResult | None = None

        for model_spec in self.model_specs:
            processor = UniversalProcessor(
                adapter_for(model_spec)
            )
            result = processor.run(
                cell_spec=self.cell_spec,
                agent_spec=self.agent_spec,
                model_spec=model_spec,
                value=value,
            )
            attempts.append(result)
            if result.status == "SUCCEEDED":
                selected = result
                break

        input_hashes = {
            item.evidence.input_sha256
            for item in attempts
        }
        input_consistent = len(input_hashes) <= 1

        status = (
            "SUCCEEDED"
            if selected is not None and input_consistent
            else "FAILED"
        )
        selected_model_id = (
            selected.evidence.model_id
            if selected is not None and input_consistent
            else None
        )
        output = (
            selected.output
            if selected is not None and input_consistent
            else None
        )
        finished_at = utc_now()

        routing_evidence = {
            "execution_id": execution_id,
            "mode": self.routing_mode,
            "attempt_count": len(attempts),
            "attempted_model_ids": [
                item.evidence.model_id
                for item in attempts
            ],
            "attempt_statuses": [
                item.status
                for item in attempts
            ],
            "selected_model_id": selected_model_id,
            "semantic_input_hash_consistent": input_consistent,
            "semantic_input_sha256": (
                next(iter(input_hashes))
                if input_consistent and input_hashes
                else None
            ),
            "fallback_used": len(attempts) > 1,
        }

        return RoutedRunResult(
            schema_version="father.routed_run_result.v0.1",
            execution_id=execution_id,
            cell_id=str(self.cell_spec["cell_id"]),
            routing_mode=self.routing_mode,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            selected_model_id=selected_model_id,
            output=output,
            attempts=attempts,
            routing_evidence=routing_evidence,
        )
