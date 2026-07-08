#!/usr/bin/env python3
"""Build a passive bus supervisor cellular snapshot from JSONL events."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.context.passive_bus_supervisor_cellular_snapshot import (
    build_cellular_snapshot,
    event_from_mapping,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_jsonl_events(path: Path) -> list[dict[str, Any]]:
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(event, dict):
                raise ValueError(f"event line {line_number} must be a JSON object")
            events.append(event)
    return events


def build_snapshot_payload(
    *,
    events_jsonl: Path,
    generated_at: str,
    source_label: str,
) -> dict[str, Any]:
    raw_events = _load_jsonl_events(events_jsonl)
    events = [event_from_mapping(event) for event in raw_events]
    snapshot = build_cellular_snapshot(
        events,
        generated_at=generated_at,
        metadata={
            "source": source_label,
            "events_jsonl": str(events_jsonl),
            "patch_id": "0220-passive_bus_supervisor_cellular_snapshot",
        },
    )
    payload = snapshot.to_dict()
    payload["cellular_snapshot_written"] = True
    payload["supervision_authority_violation"] = False
    return payload


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events-jsonl",
        required=True,
        type=Path,
        help="Path to passive bus events in JSONL format.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the cellular snapshot JSON should be written.",
    )
    parser.add_argument(
        "--generated-at",
        default="",
        help="Optional deterministic snapshot timestamp.",
    )
    parser.add_argument(
        "--source-label",
        default="passive_bus_supervisor",
        help="Metadata label for the event source.",
    )
    parser.add_argument(
        "--format",
        choices=("json",),
        default="json",
        help="Output format. JSON is the only supported format.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    generated_at = args.generated_at or _utc_now()
    payload = build_snapshot_payload(
        events_jsonl=args.events_jsonl,
        generated_at=generated_at,
        source_label=args.source_label,
    )
    _write_payload(args.output, payload)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
