#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from context.cell_snapshot_journal import write_cell_snapshots_jsonl
from context.cell_snapshot_journal_reader import read_cell_snapshot_jsonl
from context.cell_snapshot_sse import cell_journal_to_sse_text
from context.cell_snapshot_synthetic import (
    SyntheticCellPopulationConfig,
    generate_synthetic_cell_snapshots,
)


CELL_LENS_DEMO_BUNDLE_SCHEMA = "missipy.cell_lens_local_demo_bundle.v1"


@dataclass(frozen=True, slots=True)
class CellLensLocalDemoBundleResult:
    output_dir: str
    journal_path: str
    sse_preview_path: str
    snapshot_count: int
    replay_count: int
    sse_event_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_LENS_DEMO_BUNDLE_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.snapshot_count == self.replay_count

    def to_json_dict(self) -> dict[str, object]:
        return {
            "errors": list(self.errors),
            "journal_path": self.journal_path,
            "ok": self.ok,
            "output_dir": self.output_dir,
            "replay_count": self.replay_count,
            "schema": self.schema,
            "snapshot_count": self.snapshot_count,
            "sse_event_count": self.sse_event_count,
            "sse_preview_path": self.sse_preview_path,
        }


def build_cell_lens_local_demo_bundle(
    output_dir: Path,
    *,
    population_size: int = 32,
    tick_count: int = 20,
    seed: int = 42,
    sse_limit: int = 20,
) -> CellLensLocalDemoBundleResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    journal_path = output_dir / "cells.jsonl"
    sse_preview_path = output_dir / "cells.sse"
    report_path = output_dir / "report.json"

    config = SyntheticCellPopulationConfig(
        population_size=population_size,
        tick_count=tick_count,
        seed=seed,
    )
    snapshots = tuple(generate_synthetic_cell_snapshots(config))
    journal_result = write_cell_snapshots_jsonl(journal_path, snapshots)
    replay_result = read_cell_snapshot_jsonl(journal_path)
    sse_text = cell_journal_to_sse_text(journal_path, limit=sse_limit)
    sse_preview_path.write_text(sse_text, encoding="utf-8")

    errors = list(journal_result.errors)
    errors.extend(replay_result.errors)

    result = CellLensLocalDemoBundleResult(
        output_dir=str(output_dir),
        journal_path=str(journal_path),
        sse_preview_path=str(sse_preview_path),
        snapshot_count=len(snapshots),
        replay_count=len(replay_result.snapshots),
        sse_event_count=sse_text.count("\nevent: cell_snapshot\n"),
        errors=tuple(errors),
    )
    report_path.write_text(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local read-only Cell Lens demo bundle.")
    parser.add_argument("--output-dir", default=".var/cell_lens_demo")
    parser.add_argument("--population-size", type=int, default=32)
    parser.add_argument("--tick-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sse-limit", type=int, default=20)
    args = parser.parse_args()

    result = build_cell_lens_local_demo_bundle(
        Path(args.output_dir),
        population_size=args.population_size,
        tick_count=args.tick_count,
        seed=args.seed,
        sse_limit=args.sse_limit,
    )
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
