"""Adapter registry for FATHER Model Zoo runtime specs."""

from __future__ import annotations

from father_core.adapters.base import ModelAdapter
from father_core.adapters.deterministic import DeterministicTestAdapter
from father_core.adapters.failing import FailingTestAdapter
from father_core.adapters.openai_compatible import OpenAICompatibleAdapter


ADAPTERS: dict[str, type[ModelAdapter]] = {
    "deterministic_test": DeterministicTestAdapter,
    "failing_test": FailingTestAdapter,
    "openai_compatible": OpenAICompatibleAdapter,
}


def adapter_for(model_spec: dict) -> ModelAdapter:
    provider_type = str(model_spec.get("provider_type") or "")
    adapter_cls = ADAPTERS.get(provider_type)
    if not adapter_cls:
        raise ValueError(
            f"MODEL_ADAPTER_NOT_REGISTERED:{provider_type}"
        )
    return adapter_cls()
