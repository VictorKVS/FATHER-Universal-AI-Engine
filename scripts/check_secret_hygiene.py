#!/usr/bin/env python3
"""Small zero-dependency secret-hygiene guard for the FATHER prototype.

This is a baseline guard, not a replacement for a dedicated secret scanner.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_FILE_PATTERNS = (
    re.compile(r"(^|/)\.env$"),
    re.compile(r"\.session(?:-journal)?$"),
    re.compile(r"\.(?:pem|p12|pfx)$", re.IGNORECASE),
)

CONTENT_PATTERNS = {
    "github_classic_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "github_fine_grained_token": re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    findings: list[str] = []

    for relative in tracked_files():
        normalized = relative.replace("\\", "/")
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.search(normalized):
                findings.append(f"forbidden tracked file: {relative}")

        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for name, pattern in CONTENT_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{name}: {relative}")

    if findings:
        print("FATHER secret hygiene: FAIL")
        for finding in findings:
            print(f" - {finding}")
        return 1

    print("FATHER secret hygiene: PASS")
    print("Note: baseline guard only; dedicated secret scanning remains required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
