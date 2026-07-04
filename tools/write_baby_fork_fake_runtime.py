#!/usr/bin/env python3
"""Write baby-fork runtime projection into a fake local runtime surface.

Usage:

    PYTHONPATH=src:. python tools/write_baby_fork_fake_runtime.py \
      .var/baby_fork_smoke/baby_fork_report.json \
      .var/baby_fork_fake_runtime
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.fake_route_transport import write_projection_to_fake_runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write baby-fork projection into a fake runtime surface.")
    parser.add_argument("report", type=Path)
    parser.add_argument("runtime_root", type=Path)
    parser.add_argument("--occurred-at", default="2026-07-04T20:00:00Z")
    parser.add_argument(
        "--append-routes",
        action="store_true",
        help="Append route messages instead of replacing existing fake route files.",
    )
    args = parser.parse_args(argv)

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"INVALID JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("INVALID JSON: report must be an object", file=sys.stderr)
        return 2

    projection = build_baby_fork_runtime_projection(
        report,
        report_uri=str(args.report),
        occurred_at=args.occurred_at,
    )
    snapshot = write_projection_to_fake_runtime(
        args.runtime_root,
        data_handles=projection.data_handles,
        events=projection.events,
        contexts=projection.contexts,
        routes=projection.routes,
        replace_routes=not args.append_routes,
    )
    print(json.dumps(snapshot.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
