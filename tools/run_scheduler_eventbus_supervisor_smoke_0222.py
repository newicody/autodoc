#!/usr/bin/env python3
"""Smoke a Scheduler upstream EventBus event into the passive supervisor sink.

This tool is a functional supervision harness. It does not depend on Scheduler implementation,
does not call Scheduler.run, and does not implement an EventBus. It builds the
canonical event shape that the existing Scheduler/EventBus path can emit, then
feeds the passive downstream sink for validation and human snapshot output.
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

from src.context.passive_bus_supervisor_cellular_snapshot import PassiveSupervisorSink


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_payload_items(items: list[str]) -> dict[str, str]:
    payload: dict[str, str] = {}
    for item in items:
        key, separator, value = item.partition("=")
        if not separator or not key.strip():
            raise ValueError(f"invalid --payload value {item!r}; expected key=value")
        payload[key.strip()] = value
    return payload


def build_scheduler_supervision_payload(
    *,
    event_id: str,
    event_kind: str,
    scheduler_ref: str,
    state: str,
    observed_at: str,
    generated_at: str,
    handler_ref: str = "",
    route_ref: str = "",
    policy_decision_id: str = "",
    artifact_ref: str = "",
    sql_ref: str = "",
    qdrant_ref: str = "",
    shm_ref: str = "",
    error: str = "",
    payload: dict[str, str] | None = None,
    output: Path | None = None,
    audit_jsonl: Path | None = None,
) -> dict[str, Any]:
    sink = PassiveSupervisorSink(
        metadata={
            "patch_id": "0222-scheduler_eventbus_supervisor_source",
            "scheduler_role": "upstream_orchestration_authority",
            "eventbus_role": "canonical_runtime_event_transport",
            "supervisor_role": "downstream_passive_sink",
        },
        audit_jsonl=audit_jsonl,
    )
    event = sink.accept_scheduler_event(
        event_id=event_id,
        event_kind=event_kind,
        scheduler_ref=scheduler_ref,
        state=state,
        observed_at=observed_at,
        handler_ref=handler_ref,
        route_ref=route_ref,
        policy_decision_id=policy_decision_id,
        artifact_ref=artifact_ref,
        sql_ref=sql_ref,
        qdrant_ref=qdrant_ref,
        shm_ref=shm_ref,
        error=error,
        payload=payload,
    )
    if output is not None:
        result = sink.write_snapshot(
            output,
            generated_at=generated_at,
            metadata={"output": str(output)},
        )
    else:
        result = sink.snapshot_payload(generated_at=generated_at)
    result["scheduler_eventbus_source_smoke"] = True
    result["accepted_event"] = event.to_dict()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--event-kind", required=True)
    parser.add_argument("--scheduler-ref", default="default")
    parser.add_argument("--handler-ref", default="")
    parser.add_argument("--state", required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--generated-at")
    parser.add_argument("--route-ref", default="")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--artifact-ref", default="")
    parser.add_argument("--sql-ref", default="")
    parser.add_argument("--qdrant-ref", default="")
    parser.add_argument("--shm-ref", default="")
    parser.add_argument("--error", default="")
    parser.add_argument(
        "--payload",
        action="append",
        default=[],
        help="Optional payload key=value; may be repeated.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-jsonl", type=Path)
    parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    payload = build_scheduler_supervision_payload(
        event_id=args.event_id,
        event_kind=args.event_kind,
        scheduler_ref=args.scheduler_ref,
        state=args.state,
        observed_at=args.observed_at or _utc_now(),
        generated_at=args.generated_at or _utc_now(),
        handler_ref=args.handler_ref,
        route_ref=args.route_ref,
        policy_decision_id=args.policy_decision_id,
        artifact_ref=args.artifact_ref,
        sql_ref=args.sql_ref,
        qdrant_ref=args.qdrant_ref,
        shm_ref=args.shm_ref,
        error=args.error,
        payload=_parse_payload_items(args.payload),
        output=args.output,
        audit_jsonl=args.audit_jsonl,
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
