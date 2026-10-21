#!/usr/bin/env python3
"""FATHER zero-dependency DevSecOps baseline.

This is a bootstrap control, not a replacement for dedicated SAST/SCA tools.
It:
- scans Python/JS for a small fail-closed dangerous-pattern set;
- inventories dependency manifests and blocks unmanaged dependency introduction;
- emits an SPDX 2.3 SBOM for the prototype application itself.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "prototype" / "father-workbench"

PYTHON_FILES = (
    APP_ROOT / "server.py",
    APP_ROOT / "evidence_store.py",
    APP_ROOT / "migration_engine.py",
    APP_ROOT / "gate_engine.py",
    APP_ROOT / "state_store.py",
    APP_ROOT / "lifecycle_engine.py",
    APP_ROOT / "providers" / "base.py",
    APP_ROOT / "providers" / "github_adapter.py",
    APP_ROOT / "providers" / "gitlab_adapter.py",
    APP_ROOT / "providers" / "gitverse_adapter.py",
    APP_ROOT / "providers" / "sourcecraft_adapter.py",
    APP_ROOT / "providers" / "gitflic_adapter.py",
)
JS_FILES = (APP_ROOT / "app.js",)

DEPENDENCY_MANIFESTS = (
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
)

JS_PATTERNS = {
    "eval": re.compile(r"\beval\s*\("),
    "new_function": re.compile(r"\bnew\s+Function\s*\("),
    "document_write": re.compile(r"\bdocument\.write\s*\("),
    "inner_html_assignment_from_prompt": re.compile(
        r"\.innerHTML\s*=\s*(?:window\.)?prompt\s*\("
    ),
}

PYTHON_CALL_RULES = {
    "eval": ("eval",),
    "exec": ("exec",),
    "os.system": ("os", "system"),
    "pickle.loads": ("pickle", "loads"),
    "marshal.loads": ("marshal", "loads"),
}


def git_sha() -> str:
    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def dotted_name(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (*dotted_name(node.value), node.attr)
    return ()


def scan_python(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    findings: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = dotted_name(node.func)
            for rule, expected in PYTHON_CALL_RULES.items():
                if name == expected:
                    findings.append(
                        {
                            "rule": rule,
                            "file": path.relative_to(ROOT).as_posix(),
                            "line": getattr(node, "lineno", None),
                            "severity": "HIGH",
                        }
                    )

            if name == ("subprocess", "run") or name == ("subprocess", "Popen"):
                for keyword in node.keywords:
                    if (
                        keyword.arg == "shell"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        findings.append(
                            {
                                "rule": "subprocess_shell_true",
                                "file": path.relative_to(ROOT).as_posix(),
                                "line": getattr(node, "lineno", None),
                                "severity": "HIGH",
                            }
                        )

        if isinstance(node, ast.Call) and dotted_name(node.func) == ("urlopen",):
            if node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith("http://") and not arg.value.startswith(
                        ("http://127.0.0.1", "http://localhost")
                    ):
                        findings.append(
                            {
                                "rule": "plaintext_external_http",
                                "file": path.relative_to(ROOT).as_posix(),
                                "line": getattr(node, "lineno", None),
                                "severity": "HIGH",
                            }
                        )

    return findings


def scan_javascript(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    findings: list[dict[str, Any]] = []
    for rule, pattern in JS_PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                {
                    "rule": rule,
                    "file": path.relative_to(ROOT).as_posix(),
                    "line": line,
                    "severity": "HIGH",
                }
            )
    return findings


def dependency_inventory() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for name in DEPENDENCY_MANIFESTS:
        for path in APP_ROOT.rglob(name):
            found.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return sorted(found, key=lambda item: item["path"])


def build_spdx(commit_sha: str) -> dict[str, Any]:
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    namespace_seed = hashlib.sha256(
        f"FATHER-Project-Workbench:{commit_sha}".encode("utf-8")
    ).hexdigest()[:24]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "FATHER-Project-Workbench-SBOM",
        "documentNamespace": (
            "https://father.local/spdx/father-project-workbench/"
            + namespace_seed
        ),
        "creationInfo": {
            "created": created,
            "creators": ["Tool: FATHER DevSecOps Baseline"],
        },
        "packages": [
            {
                "name": "FATHER Project Workbench",
                "SPDXID": "SPDXRef-Package-FATHER-Workbench",
                "versionInfo": commit_sha,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "primaryPackagePurpose": "APPLICATION",
            }
        ],
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-FATHER-Workbench",
            }
        ],
        "annotations": [
            {
                "annotationDate": created,
                "annotationType": "OTHER",
                "annotator": "Tool: FATHER DevSecOps Baseline",
                "comment": (
                    "Prototype currently declares no third-party runtime "
                    "dependency manifest inside prototype/father-workbench. "
                    "This is a bootstrap SBOM, not a vulnerability scan."
                ),
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="artifacts/devsecops",
        help="Output directory relative to repository root",
    )
    args = parser.parse_args()

    output = (ROOT / args.output).resolve()
    output.relative_to(ROOT)
    output.mkdir(parents=True, exist_ok=True)

    findings: list[dict[str, Any]] = []
    for path in PYTHON_FILES:
        if path.is_file():
            findings.extend(scan_python(path))
    for path in JS_FILES:
        if path.is_file():
            findings.extend(scan_javascript(path))

    manifests = dependency_inventory()
    unmanaged_dependency_surface = bool(manifests)
    commit_sha = git_sha()

    report = {
        "schema_version": "father.devsecops.baseline.v0.1",
        "scope": "prototype/father-workbench",
        "commit_sha": commit_sha,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_sast": {
            "status": "PASS" if not findings else "FAIL",
            "finding_count": len(findings),
            "findings": findings,
            "note": "Bootstrap rules only; dedicated SAST remains required.",
        },
        "dependency_governance": {
            "status": "PASS" if not unmanaged_dependency_surface else "REVIEW_REQUIRED",
            "declared_manifest_count": len(manifests),
            "manifests": manifests,
            "external_runtime_dependency_count": 0 if not manifests else None,
            "note": (
                "No dependency manifest in prototype scope."
                if not manifests
                else "Dependency manifest detected: dedicated SCA/lock-policy must be configured."
            ),
        },
        "sbom": {
            "format": "SPDX-2.3",
            "path": "father-workbench.spdx.json",
            "vulnerability_scan": "NOT_PERFORMED",
        },
    }

    sbom = build_spdx(commit_sha)
    (output / "father-workbench.spdx.json").write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "devsecops-baseline.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if findings:
        return 1
    if unmanaged_dependency_surface:
        print(
            "FATHER dependency governance: REVIEW_REQUIRED. "
            "Do not promote until dedicated SCA is configured.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
