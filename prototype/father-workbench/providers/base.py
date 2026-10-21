"""Common provider contracts for FATHER Dev Platform adapters."""

from __future__ import annotations

import re

BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


class ProviderError(RuntimeError):
    """Provider request failed without exposing provider credentials."""


def validate_branch_name(value: str) -> str:
    branch = value.strip()
    forbidden_fragments = ("..", "//", "@{", "\\")
    forbidden_chars = set(" ~^:?*[]")
    if (
        not BRANCH_PATTERN.fullmatch(branch)
        or any(fragment in branch for fragment in forbidden_fragments)
        or any(char in branch for char in forbidden_chars)
        or branch.endswith(("/", ".", ".lock"))
    ):
        raise ValueError("Invalid branch name")
    return branch
