"""Generic OpenAI-compatible chat-completions adapter.

Can be pointed at any provider exposing a compatible /chat/completions API.
Secret values are read from the process environment and are never returned.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from father_core.adapters.base import ModelAdapter, ModelAdapterError
from father_core.contracts import ModelRequest, ModelResponse


class OpenAICompatibleAdapter(ModelAdapter):
    adapter_type = "openai_compatible"

    def _env(
        self,
        model_spec: dict[str, Any],
        field: str,
        *,
        required: bool,
    ) -> str | None:
        endpoint = model_spec.get("endpoint") or {}
        env_name = endpoint.get(field)
        if not env_name:
            if required:
                raise ModelAdapterError(f"MODEL_SPEC_MISSING_{field.upper()}")
            return None
        value = os.getenv(str(env_name))
        if required and not value:
            raise ModelAdapterError(f"MODEL_ENV_UNAVAILABLE:{env_name}")
        return value

    def generate(
        self,
        request: ModelRequest,
        model_spec: dict[str, Any],
    ) -> ModelResponse:
        endpoint = model_spec.get("endpoint") or {}
        base_url = self._env(
            model_spec,
            "base_url_env",
            required=True,
        )
        provider_model = self._env(
            model_spec,
            "model_env",
            required=True,
        )
        api_key = self._env(
            model_spec,
            "api_key_env",
            required=False,
        )
        path = str(endpoint.get("path") or "/chat/completions")
        timeout = float(endpoint.get("timeout_seconds") or 60)

        payload = {
            "model": provider_model,
            "messages": request.messages,
            **request.parameters,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "FATHER-Core/0.1",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        http_request = Request(
            str(base_url).rstrip("/") + path,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise ModelAdapterError(
                f"MODEL_HTTP_{exc.code}"
            ) from None
        except URLError:
            raise ModelAdapterError("MODEL_NETWORK_ERROR") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ModelAdapterError("MODEL_INVALID_JSON") from None

        choices = raw.get("choices") or []
        if not choices:
            raise ModelAdapterError("MODEL_RESPONSE_NO_CHOICES")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise ModelAdapterError("MODEL_RESPONSE_NO_TEXT")

        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        return ModelResponse(
            model_id=request.model_id,
            content=content,
            provider_response_id=raw.get("id"),
            usage=usage,
            metadata={
                "provider_model": provider_model,
                "finish_reason": choices[0].get("finish_reason"),
            },
        )
