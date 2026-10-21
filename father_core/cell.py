"""Minimal FATHER factory-cell runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from father_core.adapters.base import ModelAdapter
from father_core.adapters.deterministic import (
    DeterministicTestAdapter,
)
from father_core.adapters.openai_compatible import (
    OpenAICompatibleAdapter,
)
from father_core.processor import UniversalProcessor
from father_core.zoo import Zoo


ADAPTERS = {
    "deterministic_test": DeterministicTestAdapter,
    "openai_compatible": OpenAICompatibleAdapter,
}


class FactoryCell:
    def __init__(
        self,
        *,
        repo_root: Path,
        cell_id: str,
        test_mode: bool = False,
        adapter: ModelAdapter | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.zoo = Zoo(self.repo_root)
        self.cell_spec = self.zoo.cell(cell_id)
        self.agent_spec = self.zoo.agent(
            str(self.cell_spec["agent_id"])
        )

        model_key = (
            "test_model_id"
            if test_mode
            else "model_id"
        )
        model_id = str(self.cell_spec[model_key])
        self.model_spec = self.zoo.model(model_id)

        if adapter is None:
            provider_type = str(
                self.model_spec.get("provider_type") or ""
            )
            adapter_cls = ADAPTERS.get(provider_type)
            if not adapter_cls:
                raise ValueError(
                    f"MODEL_ADAPTER_NOT_REGISTERED:{provider_type}"
                )
            adapter = adapter_cls()
        self.processor = UniversalProcessor(adapter)

    def run(self, value: Any):
        return self.processor.run(
            cell_spec=self.cell_spec,
            agent_spec=self.agent_spec,
            model_spec=self.model_spec,
            value=value,
        )
