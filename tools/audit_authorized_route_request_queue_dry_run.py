#!/usr/bin/env python3
"""Dry-run audit an authorized scheduler route entry handoff queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue_dry_run import audit_authorized_route_request_queue_dry_run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run audit scheduler.route_requests.jsonl without route execution."
    )
    parser.add_argument("--queue", required=True, help="Path to scheduler.route_requests.jsonl.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root used for handler surface presence checks.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = audit_authorized_route_request_queue_dry_run(
        Path(args.queue),
        repo_root=Path(args.repo_root),
    )

    if args.format == "json":
        print(json.dumps(report.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"item_count: {report.item_count}")
        print(f"ready_count: {report.ready_count}")
        print(f"blocked_count: {report.blocked_count}")
        print("dry_run_only: True")
        print("scheduler_modified: False")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
