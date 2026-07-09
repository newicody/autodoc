#!/usr/bin/env python3
"""Build a Scheduler-owned runtime registry from the 0256 source map."""

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

from context.scheduler_owned_runtime_registry_0257 import (  # noqa: E402
    build_scheduler_owned_runtime_registry,
    load_source_map_payload,
    write_scheduler_owned_runtime_registry_report,
)


DEFAULT_SOURCE_MAP = ROOT / ".var/reports/scheduler_owned_runtime_reuse_source_map_0256.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-map", default=str(DEFAULT_SOURCE_MAP))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_map_path = Path(args.source_map)
    source_map_payload = load_source_map_payload(source_map_path) if source_map_path.exists() else None

    if args.output:
        payload = write_scheduler_owned_runtime_registry_report(
            Path(args.output),
            source_map_payload,
        )
    else:
        payload = build_scheduler_owned_runtime_registry(source_map_payload).to_dict()

    if args.format == "summary":
        components = ",".join(item["component_id"] for item in payload["registrations"])
        print(
            "scheduler_owned_runtime_registry_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"source_map_complete={payload['source_map_complete']} components={components}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
