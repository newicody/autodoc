#!/usr/bin/env python3
"""Run baby-fork report -> fake runtime -> recorder journal.

Usage:

    PYTHONPATH=src:. python tools/run_baby_fork_runtime_flow.py \
      .var/baby_fork_smoke/baby_fork_report.json \
      .var/baby_fork_fake_runtime \
      .var/baby_fork_fake_runtime/runtime_journal.jsonl \
      --controlfs-root .var/baby_fork_controlfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from context.baby_fork_runtime_flow import run_baby_fork_runtime_flow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run baby-fork runtime flow from an existing report.")
    parser.add_argument("report_path", type=Path)
    parser.add_argument("fake_runtime_root", type=Path)
    parser.add_argument("journal_path", type=Path)
    parser.add_argument("--occurred-at", default="2026-07-04T20:00:00Z")
    parser.add_argument("--append-journal", action="store_true")
    parser.add_argument("--controlfs-root", type=Path)
    parser.add_argument("--context-id")
    args = parser.parse_args(argv)

    try:
        summary = run_baby_fork_runtime_flow(
            args.report_path,
            args.fake_runtime_root,
            args.journal_path,
            occurred_at=args.occurred_at,
            append_journal=args.append_journal,
            controlfs_root=args.controlfs_root,
            context_id=args.context_id,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
