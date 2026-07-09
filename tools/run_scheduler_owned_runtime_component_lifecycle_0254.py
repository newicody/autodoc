#!/usr/bin/env python3
"""Print or write the Scheduler-owned runtime component lifecycle model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _path in (str(SRC_ROOT), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.scheduler_owned_runtime_component_lifecycle_0254 import (  # noqa: E402
    build_scheduler_owned_runtime_lifecycle,
    validate_scheduler_owned_lifecycle,
    write_scheduler_owned_runtime_lifecycle_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output:
        payload = write_scheduler_owned_runtime_lifecycle_report(Path(args.output))
    else:
        lifecycle = build_scheduler_owned_runtime_lifecycle()
        issues = validate_scheduler_owned_lifecycle(lifecycle)
        payload = lifecycle.to_dict()
        payload["valid"] = not issues
        payload["issues"] = list(issues)

    if args.format == "summary":
        components = ",".join(component["component_id"] for component in payload["components"])
        print(
            "scheduler_owned_runtime_component_lifecycle_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"components={components}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
