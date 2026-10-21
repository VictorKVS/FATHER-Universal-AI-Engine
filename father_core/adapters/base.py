"""Model adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from father_core.contracts import ModelRequest, ModelResponse


class ModelAdapterError(RuntimeError):
    """Model invocation failed without exposing credentials or prompt secrets."""


class ModelAdapter(ABC):
    adapter_type = "abstract"

    @abstractmethod
    def generate(
        self,
        request: ModelRequest,
        model_spec: dict[str, Any],
    ) -> ModelResponse:
        raise NotImplementedError
