"""Safe text document store for registered FATHER project artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ALLOWED_ROOTS = {"docs", "projects", "config"}
ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
MAX_DOCUMENT_BYTES = 1024 * 1024


class DocumentConflictError(RuntimeError):
    """Document changed after it was loaded."""


class DocumentStore:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    @staticmethod
    def sha256_bytes(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    def resolve(self, source_ref: str) -> Path:
        raw = source_ref.strip().replace("\\", "/")
        if not raw or raw.startswith("/"):
            raise ValueError("Document source_ref must be repository-relative")

        relative = Path(raw)
        if not relative.parts or relative.parts[0] not in ALLOWED_ROOTS:
            raise ValueError("Document source_ref root is not allowed")
        if relative.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("Document file type is not allowed")

        path = (self.repo_root / relative).resolve()
        path.relative_to(self.repo_root)
        return path

    def read(self, source_ref: str) -> dict[str, Any]:
        path = self.resolve(source_ref)
        if not path.is_file():
            return {
                "source_ref": source_ref,
                "exists": False,
                "content": "",
                "sha256": "NEW",
                "size": 0,
            }
        data = path.read_bytes()
        if len(data) > MAX_DOCUMENT_BYTES:
            raise ValueError("Document exceeds maximum editor size")
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Document is not UTF-8 text") from None
        return {
            "source_ref": source_ref,
            "exists": True,
            "content": content,
            "sha256": self.sha256_bytes(data),
            "size": len(data),
        }

    @staticmethod
    def _validate_content(path: Path, content: str) -> bytes:
        if "\x00" in content:
            raise ValueError("NUL bytes are not allowed")
        data = content.encode("utf-8")
        if len(data) > MAX_DOCUMENT_BYTES:
            raise ValueError("Document exceeds maximum editor size")
        if path.suffix.lower() == ".json":
            json.loads(content)
        return data

    def write(
        self,
        source_ref: str,
        content: str,
        expected_sha256: str,
    ) -> dict[str, Any]:
        path = self.resolve(source_ref)
        current = self.read(source_ref)
        if current["sha256"] != expected_sha256:
            raise DocumentConflictError(
                "Document changed; reload before saving"
            )

        data = self._validate_content(path, content)
        new_sha = self.sha256_bytes(data)
        if current["exists"] and new_sha == current["sha256"]:
            return {
                "source_ref": source_ref,
                "old_sha256": current["sha256"],
                "new_sha256": new_sha,
                "changed": False,
                "size": len(data),
            }

        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=path.parent,
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()

        verified = self.read(source_ref)
        if verified["sha256"] != new_sha:
            raise OSError("Document verification failed after write")

        return {
            "source_ref": source_ref,
            "old_sha256": current["sha256"],
            "new_sha256": new_sha,
            "changed": True,
            "size": len(data),
        }
