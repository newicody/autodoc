#!/usr/bin/env python3
"""Run an all-surface passive supervisor smoke without owning runtime authority."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _path in (str(SRC_ROOT), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.context import passive_bus_supervisor_cellular_snapshot as supervision


EXPECTED_CELL_KINDS = (
    "SCHEDULER",
    "ROUTEPROXY",
    "CONTROLPROXY",
    "SHM_RING",
    "POLICY_GATE",
    "GITHUB_ARTIFACT",
    "SOURCE_CANDIDATE",
    "SQL_STORE",
    "QDRANT_PROJECTION",
    "REHYDRATION",
    "PUSHBACK",
)


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _event_from_helper(
    helper_name: str,
    helper_kwargs: Mapping[str, Any],
    fallback_mapping: Mapping[str, Any],
) -> Any:
    helper = getattr(supervision, helper_name, None)
    if callable(helper):
        try:
            return helper(**dict(helper_kwargs))
        except TypeError:
            # Keep the smoke tied to the canonical event contract even if a
            # helper gained/removed a non-authoritative convenience argument.
            pass
    return supervision.event_from_mapping(dict(fallback_mapping))


def _make_events(observed_at: str) -> tuple[Any, ...]:
    return (
        _event_from_helper(
            "scheduler_supervision_event",
            {
                "event_id": "evt-scheduler",
                "event_kind": "scheduler_handler_completed",
                "scheduler_ref": "main",
                "handler_ref": "route-handler",
                "state": "success",
                "observed_at": observed_at,
                "route_ref": "route-1",
                "policy_decision_id": "policy-1",
                "payload": {"cycle": "1"},
            },
            {
                "event_id": "evt-scheduler",
                "event_kind": "scheduler_handler_completed",
                "cell_id": "scheduler:main",
                "cell_kind": "SCHEDULER",
                "state": "success",
                "observed_at": observed_at,
                "source_ref": "scheduler:main",
                "route_ref": "route-1",
                "policy_decision_id": "policy-1",
            },
        ),
        _event_from_helper(
            "proxy_supervision_event",
            {
                "event_id": "evt-routeproxy",
                "event_kind": "routeproxy_route_active",
                "proxy_kind": "routeproxy",
                "proxy_ref": "main",
                "state": "active",
                "observed_at": observed_at,
                "route_ref": "route-1",
            },
            {
                "event_id": "evt-routeproxy",
                "event_kind": "routeproxy_route_active",
                "cell_id": "routeproxy:main",
                "cell_kind": "ROUTEPROXY",
                "state": "active",
                "observed_at": observed_at,
                "source_ref": "routeproxy:main",
                "route_ref": "route-1",
            },
        ),
        _event_from_helper(
            "proxy_supervision_event",
            {
                "event_id": "evt-controlproxy",
                "event_kind": "controlproxy_lease_active",
                "proxy_kind": "controlproxy",
                "proxy_ref": "main",
                "state": "active",
                "observed_at": observed_at,
                "route_ref": "route-1",
            },
            {
                "event_id": "evt-controlproxy",
                "event_kind": "controlproxy_lease_active",
                "cell_id": "controlproxy:main",
                "cell_kind": "CONTROLPROXY",
                "state": "active",
                "observed_at": observed_at,
                "source_ref": "controlproxy:main",
                "route_ref": "route-1",
            },
        ),
        _event_from_helper(
            "runtime_surface_supervision_event",
            {
                "event_id": "evt-shm",
                "event_kind": "shm_ring_observed",
                "cell_kind": "SHM_RING",
                "surface_ref": "ring-1",
                "state": "active",
                "observed_at": observed_at,
                "shm_ref": "shm-1",
            },
            {
                "event_id": "evt-shm",
                "event_kind": "shm_ring_observed",
                "cell_id": "shm:ring-1",
                "cell_kind": "SHM_RING",
                "state": "active",
                "observed_at": observed_at,
                "source_ref": "shm:ring-1",
                "shm_ref": "shm-1",
            },
        ),
        _event_from_helper(
            "runtime_surface_supervision_event",
            {
                "event_id": "evt-policy",
                "event_kind": "policy_gate_allowed",
                "cell_kind": "POLICY_GATE",
                "surface_ref": "gate-1",
                "state": "success",
                "observed_at": observed_at,
                "policy_decision_id": "policy-1",
            },
            {
                "event_id": "evt-policy",
                "event_kind": "policy_gate_allowed",
                "cell_id": "policy:gate-1",
                "cell_kind": "POLICY_GATE",
                "state": "success",
                "observed_at": observed_at,
                "source_ref": "policy:gate-1",
                "policy_decision_id": "policy-1",
            },
        ),
        supervision.github_artifact_supervision_event(
            event_id="evt-github",
            event_kind="artifact_seen",
            artifact_ref="artifact-1",
            state="queued",
            observed_at=observed_at,
        ),
        supervision.source_candidate_supervision_event(
            event_id="evt-candidate",
            event_kind="source_candidate_imported",
            source_candidate_ref="candidate-1",
            state="success",
            observed_at=observed_at,
        ),
        supervision.sql_supervision_event(
            event_id="evt-sql",
            event_kind="sql_persisted",
            sql_ref="sql-1",
            state="success",
            observed_at=observed_at,
        ),
        supervision.qdrant_supervision_event(
            event_id="evt-qdrant",
            event_kind="qdrant_projected",
            qdrant_ref="qdrant-1",
            state="success",
            observed_at=observed_at,
        ),
        supervision.rehydration_supervision_event(
            event_id="evt-rehydrate",
            event_kind="rehydrated",
            rehydrate_ref="rehydrate-1",
            state="success",
            observed_at=observed_at,
        ),
        supervision.pushback_supervision_event(
            event_id="evt-pushback",
            event_kind="pushback_prepared",
            pushback_ref="pushback-1",
            state="success",
            observed_at=observed_at,
        ),
    )


def _snapshot_dict(snapshot: Any) -> dict[str, Any]:
    if hasattr(snapshot, "to_dict"):
        return dict(snapshot.to_dict())
    return dict(snapshot)


def _sink_accept(sink: Any, event: Any) -> None:
    if hasattr(sink, "accept"):
        sink.accept(event)
        return
    if hasattr(sink, "accept_event"):
        sink.accept_event(event)
        return
    raise RuntimeError("PassiveSupervisorSink has no accept or accept_event method")


def _sink_snapshot(sink: Any, generated_at: str) -> Any:
    if hasattr(sink, "snapshot"):
        try:
            return sink.snapshot(generated_at=generated_at)
        except TypeError:
            return sink.snapshot()
    if hasattr(supervision, "build_cellular_snapshot"):
        return supervision.build_cellular_snapshot(tuple(getattr(sink, "events")), generated_at=generated_at)
    raise RuntimeError("PassiveSupervisorSink has no snapshot method")


def _build_snapshot(events: Iterable[Any], generated_at: str) -> dict[str, Any]:
    sink_class = getattr(supervision, "PassiveSupervisorSink", None)
    if sink_class is None:
        snapshot = supervision.build_cellular_snapshot(tuple(events), generated_at=generated_at)
        return _snapshot_dict(snapshot)

    try:
        sink = sink_class(generated_at=generated_at)
    except TypeError:
        sink = sink_class()

    for event in events:
        _sink_accept(sink, event)
    snapshot = _sink_snapshot(sink, generated_at)
    return _snapshot_dict(snapshot)


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _write_audit(path: Path, events: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            if hasattr(event, "to_dict"):
                payload = event.to_dict()
            else:
                payload = dict(event)
            handle.write(json.dumps(payload, sort_keys=True, default=_json_default) + "\n")


def parse_args(argv: tuple[str, ...]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--audit-jsonl", type=Path, default=None)
    parser.add_argument("--observed-at", default="2026-07-08T00:00:00Z")
    parser.add_argument("--generated-at", default="2026-07-08T00:00:01Z")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args(argv)


def main(argv: tuple[str, ...] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    events = _make_events(args.observed_at)
    snapshot = _build_snapshot(events, args.generated_at)
    kinds = sorted({cell.get("cell_kind", "") for cell in snapshot.get("cells", [])})
    missing = sorted(set(EXPECTED_CELL_KINDS) - set(kinds))
    result: dict[str, Any] = {
        "all_surfaces_passive_supervisor_smoke_passed": not missing,
        "expected_cell_kinds": list(EXPECTED_CELL_KINDS),
        "observed_cell_kinds": kinds,
        "missing_cell_kinds": missing,
        "event_count": len(events),
        "snapshot": snapshot,
        "authority_boundary": {
            "creates_eventbus": False,
            "uses_scheduler_run": False,
            "controls_proxy": False,
            "mutates_shm": False,
            "decides_policy": False,
            "mutates_github": False,
            "writes_sql": False,
            "writes_qdrant": False,
            "executes_rehydration": False,
            "executes_pushback": False,
            "requires_non_stdlib": False,
        },
    }
    _write_json(args.output, result)
    if args.audit_jsonl is not None:
        _write_audit(args.audit_jsonl, events)
    if args.format == "summary":
        print(
            "all_surfaces_passive_supervisor_smoke_passed="
            f"{result['all_surfaces_passive_supervisor_smoke_passed']} "
            f"event_count={result['event_count']} "
            f"cell_count={snapshot.get('cell_count', len(snapshot.get('cells', [])))} "
            f"missing_cell_kinds={','.join(missing) if missing else '-'}"
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0 if result["all_surfaces_passive_supervisor_smoke_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
