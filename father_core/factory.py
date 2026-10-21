"""Factory-cell constructor."""

from __future__ import annotations

from pathlib import Path

from father_core.cell import FactoryCell
from father_core.compare import CompareFactoryCell
from father_core.routed import RoutedFactoryCell
from father_core.zoo import Zoo


def build_cell(
    *,
    repo_root: Path,
    cell_id: str,
    test_mode: bool = False,
):
    spec = Zoo(repo_root).cell(cell_id)
    mode = str(spec.get("mode") or "")
    if mode == "SINGLE_AGENT_SINGLE_MODEL":
        return FactoryCell(
            repo_root=repo_root,
            cell_id=cell_id,
            test_mode=test_mode,
        )
    if mode == "PRIMARY_FALLBACK":
        return RoutedFactoryCell(
            repo_root=repo_root,
            cell_id=cell_id,
            test_mode=test_mode,
        )
    if mode == "FAN_OUT_COMPARE":
        return CompareFactoryCell(
            repo_root=repo_root,
            cell_id=cell_id,
            test_mode=test_mode,
        )
    raise ValueError(f"CELL_MODE_NOT_SUPPORTED:{mode}")
