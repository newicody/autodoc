#!/usr/bin/env python3
"""Check qdrant-client dependency readiness without opening a connection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _path in (str(SRC), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from inference.qdrant_client_projection_executor import inspect_qdrant_client_dependency  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_qdrant_client_dependency()
    payload = result.to_mapping()
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.format == "summary":
        print(
            "qdrant_client_projection_executor_ready="
            f"{payload['valid']} installed={payload['installed']} "
            f"version={payload['version'] or '-'} required={payload['required_version']} "
            "network_used=False qdrant_called=False touches_shm=False"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
