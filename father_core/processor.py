"""Provider-neutral universal information processor."""

from __future__ import annotations

import json
import uuid
from typing import Any

from father_core.adapters.base import ModelAdapter, ModelAdapterError
from father_core.contracts import (
    MessageEnvelope,
    ModelRequest,
    RunEvidence,
    RunResult,
    message_content_digest,
    utc_now,
)


class UniversalProcessor:
    processor_id = "FATHER_UNIVERSAL_PROCESSOR_V0_1"

    def __init__(self, adapter: ModelAdapter) -> None:
        self.adapter = adapter

    @staticmethod
    def normalize_input(value: Any, run_id: str) -> MessageEnvelope:
        if isinstance(value, str):
            content_type = "text/plain"
            payload: Any = value
        elif isinstance(value, (dict, list)):
            content_type = "application/json"
            payload = value
        else:
            raise TypeError("UNSUPPORTED_INPUT_TYPE")

        return MessageEnvelope.create(
            run_id=run_id,
            direction="INPUT",
            content_type=content_type,
            payload=payload,
            provenance={"source": "runtime_input"},
            constraints={"hidden_reasoning_persistence": False},
        )

    @staticmethod
    def _user_content(envelope: MessageEnvelope) -> str:
        if envelope.content_type == "application/json":
            return json.dumps(
                envelope.payload,
                ensure_ascii=False,
                sort_keys=True,
            )
        return str(envelope.payload)

    @staticmethod
    def build_request(
        *,
        run_id: str,
        agent_spec: dict[str, Any],
        model_spec: dict[str, Any],
        input_envelope: MessageEnvelope,
    ) -> ModelRequest:
        instructions = agent_spec.get("instructions") or []
        if not isinstance(instructions, list):
            raise ValueError("AGENT_INSTRUCTIONS_MUST_BE_LIST")

        system = "\n".join(str(item) for item in instructions)
        if not system.strip():
            raise ValueError("AGENT_INSTRUCTIONS_REQUIRED")

        return ModelRequest(
            run_id=run_id,
            model_id=str(model_spec["model_id"]),
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": UniversalProcessor._user_content(
                        input_envelope
                    ),
                },
            ],
            parameters={
                "temperature": 0.2,
            },
        )

    def run(
        self,
        *,
        cell_spec: dict[str, Any],
        agent_spec: dict[str, Any],
        model_spec: dict[str, Any],
        value: Any,
    ) -> RunResult:
        run_id = f"RUN-{uuid.uuid4().hex[:16].upper()}"
        started_at = utc_now()
        transformations = [
            "INPUT_NORMALIZE",
            "AGENT_CONTEXT_BUILD",
            "MODEL_REQUEST_BUILD",
        ]
        input_envelope = self.normalize_input(value, run_id)
        request = self.build_request(
            run_id=run_id,
            agent_spec=agent_spec,
            model_spec=model_spec,
            input_envelope=input_envelope,
        )

        output_envelope: MessageEnvelope | None = None
        model_response = None
        error_code: str | None = None
        status = "FAILED"

        try:
            model_response = self.adapter.generate(
                request,
                model_spec,
            )
            transformations.append("MODEL_INVOKE")
            output_envelope = MessageEnvelope.create(
                run_id=run_id,
                direction="OUTPUT",
                content_type="text/plain",
                payload=model_response.content,
                metadata={
                    "agent_id": agent_spec["agent_id"],
                    "model_id": model_spec["model_id"],
                    "processor_id": self.processor_id,
                },
                provenance={
                    "model_response_id": (
                        model_response.provider_response_id
                    ),
                },
                constraints={
                    "hidden_reasoning_persistence": False,
                },
            )
            transformations.append("OUTPUT_NORMALIZE")
            status = "SUCCEEDED"
        except (
            ModelAdapterError,
            TypeError,
            ValueError,
        ) as exc:
            error_code = str(exc).split(":", 1)[0] or "PROCESSING_FAILED"

        finished_at = utc_now()
        evidence = RunEvidence(
            schema_version="father.run_evidence.v0.1",
            run_id=run_id,
            cell_id=str(cell_spec["cell_id"]),
            agent_id=str(agent_spec["agent_id"]),
            model_id=str(model_spec["model_id"]),
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            input_sha256=message_content_digest(input_envelope),
            output_sha256=(
                message_content_digest(output_envelope)
                if output_envelope
                else None
            ),
            transformations=transformations,
            adapter_type=self.adapter.adapter_type,
            error_code=error_code,
        )
        return RunResult(
            schema_version="father.run_result.v0.1",
            run_id=run_id,
            status=status,
            input=input_envelope,
            output=output_envelope,
            evidence=evidence,
            model_response=model_response,
            error_code=error_code,
        )
