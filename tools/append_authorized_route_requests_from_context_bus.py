#!/usr/bin/env python3
"""Append authorized scheduler route entries from context.bus JSONL to a handoff queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue import (  # noqa: E402
    append_authorized_route_requests_from_context_bus,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append authorized route entries from context.bus JSONL to scheduler.route_requests.jsonl."
    )
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--runtime-root", required=True, help="Runtime root where the handoff queue is written.")
    parser.add_argument("--policy-decision-id", required=True, help="Explicit policy decision id.")
    parser.add_argument("--priority", type=int, default=50, help="Scheduler candidate priority, 0..100.")
    parser.add_argument("--queue-name", default="scheduler.route_requests.jsonl", help="Local JSONL queue filename.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = append_authorized_route_requests_from_context_bus(
        context_bus_path=Path(args.context_bus),
        runtime_root=Path(args.runtime_root),
        policy_decision_id=args.policy_decision_id,
        priority=args.priority,
        queue_name=args.queue_name,
    )

    if args.format == "json":
        print(json.dumps(report.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"queued_count: {report.queued_count}")
        print(f"queue_path: {report.queue_path}")
        print("authorized_only: True")
        print("scheduler_modified: False")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
