#!/usr/bin/env python3
"""Build a baby-fork RouteProxy dry-run plan from ControlFS desired manifests.

Usage:

    PYTHONPATH=src:. python tools/baby_fork_routeproxy_plan.py \
      .var/baby_fork_controlfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.baby_fork_controlfs import (
    baby_fork_controlfs_summary,
    build_baby_fork_routeproxy_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build baby-fork RouteProxy dry-run plan.")
    parser.add_argument("controlfs_root", type=Path)
    parser.add_argument("--context-id", default="baby_fork_smoke")
    parser.add_argument("--include-noop", action="store_true")
    parser.add_argument(
        "--no-write-desired",
        action="store_true",
        help="Do not create/update desired manifests before building the plan.",
    )
    args = parser.parse_args(argv)

    plan = build_baby_fork_routeproxy_plan(
        args.controlfs_root,
        context_id=args.context_id,
        include_noop=args.include_noop,
        write_desired=not args.no_write_desired,
    )
    print(json.dumps(baby_fork_controlfs_summary(args.controlfs_root, plan), indent=2, sort_keys=True))
    return 1 if plan.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
