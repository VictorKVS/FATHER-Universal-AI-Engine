"""Forced failure adapter used to prove fallback routing."""

from __future__ import annotations

from typing import Any

from father_core.adapters.base import ModelAdapter, ModelAdapterError
from father_core.contracts import ModelRequest, ModelResponse


class FailingTestAdapter(ModelAdapter):
    adapter_type = "failing_test"

    def generate(
        self,
        request: ModelRequest,
        model_spec: dict[str, Any],
    ) -> ModelResponse:
        raise ModelAdapterError("TEST_FORCED_FAILURE")
