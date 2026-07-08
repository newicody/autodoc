#!/usr/bin/env python3
"""Build a passive bus supervisor cellular snapshot from passive events.

The direct EventBus sink is the canonical path. JSON/JSONL inputs in this tool
are replay and test harnesses only; they are not the runtime hot path.
"""

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
    PassiveSupervisorSink,
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


def _load_json_event(raw_json: str) -> dict[str, Any]:
    try:
        event = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid --event-json value: {exc}") from exc
    if not isinstance(event, dict):
        raise ValueError("--event-json must be a JSON object")
    return event


def build_snapshot_payload(
    *,
    events_jsonl: Path | None = None,
    event_mappings: list[dict[str, Any]] | None = None,
    generated_at: str,
    source_label: str,
    audit_jsonl: Path | None = None,
) -> dict[str, Any]:
    sink = PassiveSupervisorSink(
        metadata={
            "source": source_label,
            "patch_id": "0221-bus_direct_passive_supervisor_sink",
            "runtime_path": "eventbus_direct_sink",
            "jsonl_role": "optional_replay_or_audit_only",
        },
        audit_jsonl=audit_jsonl,
    )
    accepted = 0
    if events_jsonl is not None:
        for event in _load_jsonl_events(events_jsonl):
            sink.accept(event)
            accepted += 1
    for event in event_mappings or []:
        sink.accept(event)
        accepted += 1
    if accepted == 0:
        raise ValueError("at least one EventBus event is required")

    metadata = {}
    if events_jsonl is not None:
        metadata["events_jsonl"] = str(events_jsonl)
    payload = sink.snapshot_payload(generated_at=generated_at, metadata=metadata)
    return payload


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--events-jsonl",
        type=Path,
        help=(
            "Optional replay input with canonical EventBus events in JSONL format. "
            "This is not the runtime hot path."
        ),
    )
    parser.add_argument(
        "--event-json",
        action="append",
        default=[],
        help=(
            "Optional single canonical EventBus event JSON object. May be repeated "
            "for fileless smoke tests."
        ),
    )
    parser.add_argument(
        "--audit-jsonl",
        type=Path,
        help="Optional audit/replay journal written by the passive sink.",
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
        default="eventbus_passive_supervisor_sink",
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
    event_mappings = [_load_json_event(value) for value in args.event_json]
    payload = build_snapshot_payload(
        events_jsonl=args.events_jsonl,
        event_mappings=event_mappings,
        generated_at=generated_at,
        source_label=args.source_label,
        audit_jsonl=args.audit_jsonl,
    )
    payload["cellular_snapshot_written"] = True
    _write_payload(args.output, payload)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
