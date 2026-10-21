#!/usr/bin/env python3
"""Run a FATHER factory cell from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from father_core import FactoryCell


def parse_value(args: argparse.Namespace):
    if args.json_input is not None:
        return json.loads(args.json_input)
    return args.input


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a FATHER universal processing cell"
    )
    parser.add_argument("--cell", default="CELL-001")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use the deterministic contract-test model",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Plain text input")
    group.add_argument("--json-input", help="JSON input")
    parser.add_argument(
        "--output",
        help="Optional JSON file for the full RunResult",
    )
    args = parser.parse_args()

    try:
        value = parse_value(args)
        cell = FactoryCell(
            repo_root=REPO_ROOT,
            cell_id=args.cell,
            test_mode=args.test,
        )
        result = cell.run(value)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_code": str(exc).split(":", 1)[0],
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    payload = result.to_dict()
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )
    print(rendered)

    if args.output:
        path = Path(args.output)
        if not path.is_absolute():
            path = REPO_ROOT / path
        path = path.resolve()
        try:
            path.relative_to(REPO_ROOT)
        except ValueError:
            print(
                '{"status":"FAILED","error_code":"OUTPUT_OUTSIDE_REPOSITORY"}',
                file=sys.stderr,
            )
            return 2
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")

    return 0 if result.status == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
