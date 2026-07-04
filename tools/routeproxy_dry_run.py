#!/usr/bin/env python3
"""Build a RouteProxy dry-run plan from a ControlFS root.

Usage:

    PYTHONPATH=src:. python tools/routeproxy_dry_run.py /run/autodoc/controlfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.routeproxy_reconciler import build_routeproxy_plan, summarize_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a RouteProxy dry-run reconciliation plan.")
    parser.add_argument("controlfs_root", type=Path)
    parser.add_argument("--include-noop", action="store_true", help="Include matching desired/active routes.")
    parser.add_argument("--summary", action="store_true", help="Print only action counts.")
    args = parser.parse_args(argv)

    plan = build_routeproxy_plan(args.controlfs_root, include_noop=args.include_noop)

    if args.summary:
        print(json.dumps(summarize_plan(plan), indent=2, sort_keys=True))
    else:
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))

    return 1 if plan.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
