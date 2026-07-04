#!/usr/bin/env python3
"""Ingest a fake local runtime surface into a recorder journal JSONL file.

Usage:

    PYTHONPATH=src:. python tools/record_fake_runtime.py \
      .var/baby_fork_fake_runtime \
      .var/baby_fork_fake_runtime/runtime_journal.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.fake_runtime_recorder import ingest_fake_runtime_to_journal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record fake runtime messages into a JSONL journal.")
    parser.add_argument("runtime_root", type=Path)
    parser.add_argument("journal_path", type=Path)
    parser.add_argument("--append", action="store_true", help="Append instead of replacing the journal.")
    args = parser.parse_args(argv)

    summary = ingest_fake_runtime_to_journal(
        args.runtime_root,
        args.journal_path,
        append=args.append,
    )
    print(json.dumps(summary.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
