#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.cell_observation_event import CellObservationEvent
from context.cell_snapshot_journal import write_cell_snapshots_jsonl


def read_observation_events_jsonl(path: Path, *, strict: bool = False) -> tuple[CellObservationEvent, ...]:
    events: list[CellObservationEvent] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                events.append(CellObservationEvent.from_json_line(stripped))
            except Exception:
                if strict:
                    raise
                continue
    return tuple(events)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert recorded cell observation events to a cell snapshot journal.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    events = read_observation_events_jsonl(Path(args.input), strict=args.strict)
    result = write_cell_snapshots_jsonl(
        Path(args.output),
        (event.to_cell_snapshot() for event in events),
        strict=args.strict,
    )
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
