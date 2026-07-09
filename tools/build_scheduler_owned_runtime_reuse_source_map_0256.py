#!/usr/bin/env python3
"""Build the filtered source map for Scheduler-owned runtime reuse."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.scheduler_owned_runtime_reuse_source_map_0256 import (  # noqa: E402
    build_scheduler_owned_runtime_reuse_source_map,
    write_scheduler_owned_runtime_reuse_source_map_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if args.output:
        payload = write_scheduler_owned_runtime_reuse_source_map_report(root, Path(args.output))
    else:
        payload = build_scheduler_owned_runtime_reuse_source_map(root).to_dict()

    if args.format == "summary":
        missing = ",".join(payload["missing_surfaces"]) or "-"
        selected = ",".join(
            f"{item['surface']}:{len(item['primary_paths'])}"
            for item in payload["selections"]
        )
        print(
            "scheduler_owned_runtime_reuse_source_map_complete="
            f"{payload['complete']} missing={missing} {selected}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
