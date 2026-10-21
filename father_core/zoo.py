"""Safe loaders for Agent / Model / Cell Zoo runtime records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ZooError(RuntimeError):
    pass


class Zoo:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def _json(self, relative_path: str) -> dict[str, Any]:
        path = (self.repo_root / relative_path).resolve()
        try:
            path.relative_to(self.repo_root)
        except ValueError:
            raise ZooError("ZOO_PATH_OUTSIDE_REPOSITORY") from None
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ZooError("ZOO_RECORD_MUST_BE_OBJECT")
        return value

    @staticmethod
    def _find(
        registry: dict[str, Any],
        collection: str,
        key: str,
        value: str,
    ) -> dict[str, Any]:
        for item in registry.get(collection, []):
            if item.get(key) == value:
                return item
        raise ZooError(f"ZOO_ITEM_NOT_FOUND:{value}")

    def agent(self, agent_id: str) -> dict[str, Any]:
        registry = self._json("agents/zoo.json")
        item = self._find(
            registry,
            "agents",
            "agent_id",
            agent_id,
        )
        runtime_ref = item.get("runtime_ref")
        if not runtime_ref:
            raise ZooError(f"AGENT_RUNTIME_NOT_READY:{agent_id}")
        spec = self._json(str(runtime_ref))
        if spec.get("agent_id") != agent_id:
            raise ZooError("AGENT_ID_MISMATCH")
        return spec

    def model(self, model_id: str) -> dict[str, Any]:
        registry = self._json("models/zoo.json")
        item = self._find(
            registry,
            "models",
            "model_id",
            model_id,
        )
        spec = self._json(str(item["runtime_ref"]))
        if spec.get("model_id") != model_id:
            raise ZooError("MODEL_ID_MISMATCH")
        return spec

    def cell(self, cell_id: str) -> dict[str, Any]:
        registry = self._json("cells/zoo.json")
        item = self._find(
            registry,
            "cells",
            "cell_id",
            cell_id,
        )
        spec = self._json(str(item["runtime_ref"]))
        if spec.get("cell_id") != cell_id:
            raise ZooError("CELL_ID_MISMATCH")
        return spec
