#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from context.cell_snapshot_journal import write_cell_snapshots_jsonl
from context.cell_snapshot_synthetic import (
    SyntheticCellPopulationConfig,
    generate_synthetic_cell_snapshots,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a synthetic missipy.cell.v1 JSONL journal.")
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--population-size", type=int, default=32)
    parser.add_argument("--tick-count", type=int, default=10)
    parser.add_argument("--tick-seconds", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-observed-at", default="2026-07-03T10:00:00Z")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    config = SyntheticCellPopulationConfig(
        population_size=args.population_size,
        tick_count=args.tick_count,
        tick_seconds=args.tick_seconds,
        seed=args.seed,
        base_observed_at=args.base_observed_at,
    )
    snapshots = generate_synthetic_cell_snapshots(config)
    result = write_cell_snapshots_jsonl(Path(args.output), snapshots, strict=args.strict)
    print(result.to_json_dict())
    return 0 if result.errors == () else 1


if __name__ == "__main__":
    raise SystemExit(main())
