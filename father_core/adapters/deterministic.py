"""Deterministic adapter used only for contract tests."""

from __future__ import annotations

from typing import Any

from father_core.adapters.base import ModelAdapter
from father_core.contracts import ModelRequest, ModelResponse


class DeterministicTestAdapter(ModelAdapter):
    adapter_type = "deterministic_test"

    def generate(
        self,
        request: ModelRequest,
        model_spec: dict[str, Any],
    ) -> ModelResponse:
        user_messages = [
            item.get("content", "")
            for item in request.messages
            if item.get("role") == "user"
        ]
        content = user_messages[-1] if user_messages else ""
        return ModelResponse(
            model_id=request.model_id,
            content=f"DETERMINISTIC_RESULT: {content}",
            provider_response_id="LOCAL-TEST",
            usage={"input_messages": len(request.messages)},
            metadata={
                "test_only": True,
                "provider_type": model_spec.get("provider_type"),
            },
        )
