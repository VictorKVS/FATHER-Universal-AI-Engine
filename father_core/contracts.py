"""Canonical runtime contracts for FATHER."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MessageEnvelope:
    schema_version: str
    message_id: str
    run_id: str
    direction: str
    content_type: str
    payload: Any
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        direction: str,
        content_type: str,
        payload: Any,
        metadata: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> "MessageEnvelope":
        return cls(
            schema_version="father.message.v0.1",
            message_id=f"MSG-{uuid.uuid4().hex[:16].upper()}",
            run_id=run_id,
            direction=direction,
            content_type=content_type,
            payload=payload,
            created_at=utc_now(),
            metadata=metadata or {},
            provenance=provenance or {},
            constraints=constraints or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelRequest:
    run_id: str
    model_id: str
    messages: list[dict[str, str]]
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelResponse:
    model_id: str
    content: str
    provider_response_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunEvidence:
    schema_version: str
    run_id: str
    cell_id: str
    agent_id: str
    model_id: str
    started_at: str
    finished_at: str
    status: str
    input_sha256: str
    output_sha256: str | None
    transformations: list[str]
    adapter_type: str
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunResult:
    schema_version: str
    run_id: str
    status: str
    input: MessageEnvelope
    output: MessageEnvelope | None
    evidence: RunEvidence
    model_response: ModelResponse | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        return value
