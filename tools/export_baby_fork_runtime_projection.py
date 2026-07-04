#!/usr/bin/env python3
"""Export a baby-fork report as runtime schema messages.

Usage:

    PYTHONPATH=src:. python tools/export_baby_fork_runtime_projection.py \
      .var/baby_fork_smoke/baby_fork_report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project a baby-fork report to runtime messages.")
    parser.add_argument("report", type=Path, help="Path to baby_fork_report.json")
    parser.add_argument("--occurred-at", default="2026-07-04T20:00:00Z")
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
    print(json.dumps(projection.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
