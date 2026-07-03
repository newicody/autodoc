#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.cell_recorded_observation_ingest import ingest_recorded_observation_events_to_cell_journal


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest recorded cell observation events into a missipy.cell.v1 journal.")
    parser.add_argument("--source", required=True, help="Input missipy.cell_observation_event.v1 JSONL path.")
    parser.add_argument("--journal", required=True, help="Output missipy.cell.v1 JSONL journal path.")
    parser.add_argument("--state", required=True, help="Offset state file path.")
    parser.add_argument("--max-lines", type=int, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = ingest_recorded_observation_events_to_cell_journal(
        Path(args.source),
        Path(args.journal),
        Path(args.state),
        max_lines=args.max_lines,
        strict=args.strict,
    )
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
