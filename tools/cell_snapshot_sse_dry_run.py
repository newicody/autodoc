#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from context.cell_snapshot_sse import cell_journal_to_sse_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a missipy.cell.v1 JSONL journal to read-only SSE text.")
    parser.add_argument("--journal", required=True, help="Input missipy.cell.v1 JSONL journal.")
    parser.add_argument("--output", default="", help="Optional output file. Defaults to stdout.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start-sequence", type=int, default=0)
    args = parser.parse_args()

    text = cell_journal_to_sse_text(
        Path(args.journal),
        limit=args.limit,
        start_sequence=args.start_sequence,
    )

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
