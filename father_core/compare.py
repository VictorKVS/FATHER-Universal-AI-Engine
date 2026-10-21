"""Two-model fan-out comparison cell."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from father_core.adapters.registry import adapter_for
from father_core.contracts import RunResult, utc_now
from father_core.processor import UniversalProcessor
from father_core.zoo import Zoo


@dataclass(frozen=True)
class ComparisonRunResult:
    schema_version: str
    execution_id: str
    cell_id: str
    mode: str
    status: str
    started_at: str
    finished_at: str
    runs: list[RunResult]
    comparison: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CompareFactoryCell:
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
        if self.cell_spec.get("mode") != "FAN_OUT_COMPARE":
            raise ValueError("CELL_MODE_NOT_FAN_OUT_COMPARE")

        self.agent_spec = self.zoo.agent(
            str(self.cell_spec["agent_id"])
        )
        key = "test_model_ids" if test_mode else "model_ids"
        ids = self.cell_spec.get(key) or []
        if not isinstance(ids, list) or len(ids) != 2:
            raise ValueError("COMPARE_CELL_REQUIRES_EXACTLY_TWO_MODELS")
        self.model_specs = [self.zoo.model(str(item)) for item in ids]

    def run(self, value: Any) -> ComparisonRunResult:
        execution_id = f"EXEC-{uuid.uuid4().hex[:16].upper()}"
        started_at = utc_now()
        runs: list[RunResult] = []

        for spec in self.model_specs:
            result = UniversalProcessor(
                adapter_for(spec)
            ).run(
                cell_spec=self.cell_spec,
                agent_spec=self.agent_spec,
                model_spec=spec,
                value=value,
            )
            runs.append(result)

        input_hashes = [
            item.evidence.input_sha256
            for item in runs
        ]
        successful = [
            item for item in runs
            if item.status == "SUCCEEDED"
        ]
        output_hashes = [
            item.evidence.output_sha256
            for item in successful
        ]
        semantic_input_equal = len(set(input_hashes)) == 1
        both_succeeded = len(successful) == 2
        output_exact_match = (
            both_succeeded
            and len(set(output_hashes)) == 1
        )

        comparison = {
            "execution_id": execution_id,
            "model_ids": [
                item.evidence.model_id
                for item in runs
            ],
            "run_statuses": [
                item.status
                for item in runs
            ],
            "semantic_input_sha256": (
                input_hashes[0]
                if semantic_input_equal
                else None
            ),
            "semantic_input_equal": semantic_input_equal,
            "both_succeeded": both_succeeded,
            "output_sha256": output_hashes,
            "output_exact_match": output_exact_match,
            "selection_made": False,
            "selection_reason": "NO_JUDGE_IN_CELL_003",
        }

        status = (
            "SUCCEEDED"
            if semantic_input_equal and both_succeeded
            else "FAILED"
        )
        return ComparisonRunResult(
            schema_version="father.comparison_run_result.v0.1",
            execution_id=execution_id,
            cell_id=str(self.cell_spec["cell_id"]),
            mode="FAN_OUT_COMPARE",
            status=status,
            started_at=started_at,
            finished_at=utc_now(),
            runs=runs,
            comparison=comparison,
        )
