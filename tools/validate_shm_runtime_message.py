#!/usr/bin/env python3
"""Validate a SHM Runtime schema object.

Usage:

    PYTHONPATH=src:. python tools/validate_shm_runtime_message.py message.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from runtime.shm_runtime_schema import RuntimeSchemaValidationError, parse_runtime_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a SHM Runtime JSON message.")
    parser.add_argument("message", type=Path)
    parser.add_argument("--json", action="store_true", help="Print normalized message JSON.")
    args = parser.parse_args(argv)

    try:
        parsed = parse_runtime_json(args.message.read_text(encoding="utf-8"))
    except RuntimeSchemaValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(parsed.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"OK schema={parsed.schema}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
