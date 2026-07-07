#!/usr/bin/env python3
"""Read context.bus JSONL and build GitHub artifact scheduler intake plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_artifact_context_bus_scheduler_intake import (  # noqa: E402
    read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scheduler intake plans from existing context.bus JSONL GitHub artifact facts."
    )
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--policy-decision-id", help="Policy decision id required for authorized route entries.")
    parser.add_argument("--authorized", action="store_true", help="Emit authorized route entries.")
    parser.add_argument("--priority", type=int, default=50, help="Scheduler candidate priority, 0..100.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plans = read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
        Path(args.context_bus),
        policy_decision_id=args.policy_decision_id,
        authorized=args.authorized,
        priority=args.priority,
    )

    if args.format == "json":
        print(json.dumps([plan.to_mapping() for plan in plans], indent=2, sort_keys=True))
    else:
        print(f"plan_count: {len(plans)}")
        print(f"authorized: {args.authorized}")
        print("source: context.bus.jsonl")
        print("scheduler_modified: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
