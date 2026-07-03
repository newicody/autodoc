#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from context.cell_recorder_handoff import result_to_json, run_cell_recorder_handoff_dry_run


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run recorded observation events to a missipy.cell.v1 journal.")
    parser.add_argument("--input", required=True, help="Input missipy.cell_observation_event.v1 JSONL path.")
    parser.add_argument("--output", required=True, help="Output missipy.cell.v1 JSONL path.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = run_cell_recorder_handoff_dry_run(
        Path(args.input),
        Path(args.output),
        strict=args.strict,
    )
    print(result_to_json(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
