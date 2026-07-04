"""ControlProxy pump/tick.

This module implements phase 0084.

It is an explicit importable pump, not a service:

    tick_controlproxy(controlfs_root, runtime_root)

The pump reads ControlFS desired/active route state when called, uses the
RouteProxy dry-run reconciler, materializes missing active routes, and publishes
facts to event.bus/context.bus.

It deliberately does not:
- create a daemon
- start a service
- use OpenRC
- run forever
- watch ControlFS
- sleep or poll
- call Scheduler
- decide security policy
- grant leases
- implement lease handoff
- live resize mmap routes
- perform delete/drain cleanup
- implement inter-process locks
- implement VisPy
- add a CLI

It is a synchronous tick function. Scheduler or tests can call it directly.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.controlfs_manifest import RouteManifest
from runtime.controlproxy_active_routes import ActiveRouteRecord, materialize_active_route
from runtime.controlproxy_prepare import ROUTE_PREPARE_STATUS_SCHEMA, RoutePrepareDecision
from runtime.routeproxy_reconciler import RouteProxyPlan, build_routeproxy_plan
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
)


CONTROLPROXY_PUMP_EVENT_SCHEMA = "missipy.controlproxy.pump_event.v1"
CONTROLPROXY_PUMP_CONTEXT_SCHEMA = "missipy.controlproxy.pump_context.v1"
DEFAULT_TICK_AT = "2026-07-04T20:00:00Z"


class ControlProxyPumpError(RuntimeError):
    """Raised when the ControlProxy pump cannot complete a requested action."""


@dataclass(frozen=True)
class PumpActionRecord:
    """One action attempted or skipped by the pump."""

    route_id: str
    action: str
    status: str
    reason: str
    route_handle: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        payload = {
            "route_id": self.route_id,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
        }
        if self.route_handle is not None:
            payload["route_handle"] = self.route_handle
        return payload


@dataclass(frozen=True)
class ControlProxyPumpResult:
    """Result of one explicit ControlProxy pump tick."""

    controlfs_root: str
    runtime_root: str
    tick_id: str
    ticked_at: str
    plan_before: dict[str, Any]
    plan_after: dict[str, Any]
    materialized_count: int
    skipped_count: int
    error_count: int
    bus_event_count: int
    bus_context_count: int
    actions: tuple[PumpActionRecord, ...]
    active_records: tuple[ActiveRouteRecord, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "controlfs_root": self.controlfs_root,
            "runtime_root": self.runtime_root,
            "tick_id": self.tick_id,
            "ticked_at": self.ticked_at,
            "plan_before": self.plan_before,
            "plan_after": self.plan_after,
            "materialized_count": self.materialized_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "bus_event_count": self.bus_event_count,
            "bus_context_count": self.bus_context_count,
            "actions": [action.to_mapping() for action in self.actions],
            "active_records": [record.to_mapping() for record in self.active_records],
        }


def tick_controlproxy(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    tick_id: str = "tick:controlproxy:001",
    ticked_at: str = DEFAULT_TICK_AT,
    publish_bus: bool = True,
) -> ControlProxyPumpResult:
    """Run one synchronous ControlProxy pump tick.

    The pump:
    - builds a RouteProxy dry-run plan
    - materializes desired routes whose action is create
    - refuses update/delete as future generation/drain work
    - writes bus facts if requested
    - returns a structured summary

    No daemon, no service, no OpenRC and no CLI are involved.
    """

    plan_before = build_routeproxy_plan(controlfs_root, include_noop=True)
    actions: list[PumpActionRecord] = []
    records: list[ActiveRouteRecord] = []

    for item in plan_before.items:
        try:
            desired = item.desired
            if item.action == "create" and desired is not None:
                decision = route_prepare_decision_from_manifest(desired, ticked_at=ticked_at)
                record = materialize_active_route(
                    controlfs_root=controlfs_root,
                    runtime_root=runtime_root,
                    decision=decision,
                    desired_manifest=desired,
                    replace=True,
                )
                records.append(record)
                actions.append(
                    PumpActionRecord(
                        route_id=item.route_id,
                        action="materialize",
                        status="ok",
                        reason="desired route materialized as active mmap route",
                        route_handle=record.route_handle,
                    )
                )
            elif item.action == "noop":
                actions.append(
                    PumpActionRecord(
                        route_id=item.route_id,
                        action="noop",
                        status="skipped",
                        reason="desired route already matches active route",
                    )
                )
            elif item.action == "update":
                actions.append(
                    PumpActionRecord(
                        route_id=item.route_id,
                        action="update",
                        status="skipped",
                        reason="update requires next generation; live mmap resize is forbidden",
                    )
                )
            elif item.action == "delete":
                actions.append(
                    PumpActionRecord(
                        route_id=item.route_id,
                        action="delete",
                        status="skipped",
                        reason="delete/drain cleanup is deferred to lease/drain phase",
                    )
                )
            else:
                actions.append(
                    PumpActionRecord(
                        route_id=item.route_id,
                        action=str(item.action),
                        status="skipped",
                        reason=str(getattr(item, "reason", "unsupported plan action")),
                    )
                )
        except Exception as exc:  # pragma: no cover - kept to make pump robust at boundary
            actions.append(
                PumpActionRecord(
                    route_id=getattr(item, "route_id", "<unknown>"),
                    action=str(getattr(item, "action", "error")),
                    status="error",
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )

    plan_after = build_routeproxy_plan(controlfs_root, include_noop=True)
    event_count = 0
    context_count = 0
    if publish_bus:
        event_count, context_count = publish_pump_result_to_bus(
            runtime_root=runtime_root,
            result_actions=actions,
            active_records=records,
            tick_id=tick_id,
            ticked_at=ticked_at,
        )

    return ControlProxyPumpResult(
        controlfs_root=str(Path(controlfs_root)),
        runtime_root=str(Path(runtime_root)),
        tick_id=tick_id,
        ticked_at=ticked_at,
        plan_before=plan_before.to_mapping(),
        plan_after=plan_after.to_mapping(),
        materialized_count=len(records),
        skipped_count=sum(1 for action in actions if action.status == "skipped"),
        error_count=sum(1 for action in actions if action.status == "error"),
        bus_event_count=event_count,
        bus_context_count=context_count,
        actions=tuple(actions),
        active_records=tuple(records),
    )


def route_prepare_decision_from_manifest(
    manifest: RouteManifest,
    *,
    ticked_at: str = DEFAULT_TICK_AT,
    generation: int = 1,
) -> RoutePrepareDecision:
    """Build a ready ControlProxy decision from an accepted desired manifest.

    This is used by the pump after Scheduler/ControlProxy already accepted the
    desired manifest. It does not bypass security; it only reconstructs the
    concrete materialization decision from persisted desired state.
    """

    if manifest.slot_size is None or manifest.slot_count is None or manifest.max_frame_bytes is None:
        raise ControlProxyPumpError("manifest must include slot_size, slot_count and max_frame_bytes")
    if manifest.observed_frame_bytes is None:
        raise ControlProxyPumpError("manifest must include observed_frame_bytes")
    route_handle = f"{manifest.route_id}@g{generation}"
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=f"prep:{manifest.route_id}:g{generation}",
        route_id=manifest.route_id,
        route_handle=route_handle,
        task_id=manifest.task_id,
        zone=manifest.zone,
        status="ready",
        action="create_route_generation",
        reason="ControlProxy pump materialization from accepted desired manifest",
        required_frame_bytes=manifest.observed_frame_bytes,
        current_generation=None,
        next_generation=generation,
        current_slot_size=None,
        slot_size=manifest.slot_size,
        slot_count=manifest.slot_count,
        max_frame_bytes=manifest.max_frame_bytes,
        max_ring_bytes=manifest.slot_size * manifest.slot_count,
        max_prepare_ms=25,
        drain_timeout_ms=100,
        lease_switch_timeout_ms=10,
        notify=manifest.notify,
        overflow_policy=manifest.overflow_policy,
        decided_at=ticked_at,
    )


def publish_pump_result_to_bus(
    *,
    runtime_root: Path | str,
    result_actions: Iterable[PumpActionRecord],
    active_records: Iterable[ActiveRouteRecord],
    tick_id: str,
    ticked_at: str,
) -> tuple[int, int]:
    """Append pump facts to event.bus and context.bus JSONL files."""

    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)

    actions = tuple(result_actions)
    records = tuple(active_records)
    events = []
    contexts = []

    for index, action in enumerate(actions):
        topic = "controlproxy.pump.route_materialized" if action.status == "ok" else "controlproxy.pump.route_skipped"
        if action.status == "error":
            topic = "controlproxy.pump.route_error"
        events.append(
            EventBusMessage.from_mapping(
                {
                    "schema": EVENT_BUS_MESSAGE_SCHEMA,
                    "event_id": f"evt:{tick_id}:{index}",
                    "topic": topic,
                    "source": "controlproxy_pump",
                    "occurred_at": ticked_at,
                    "zone": "control",
                    "payload_schema": CONTROLPROXY_PUMP_EVENT_SCHEMA,
                    "payload": action.to_mapping(),
                }
            )
        )

    for index, record in enumerate(records):
        contexts.append(
            ContextBusMessage.from_mapping(
                {
                    "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
                    "context_id": record.task_id,
                    "context_version": index + 1,
                    "topic": "controlproxy.pump.active_route",
                    "source": "controlproxy_pump",
                    "occurred_at": ticked_at,
                    "zone": "control",
                    "payload_schema": CONTROLPROXY_PUMP_CONTEXT_SCHEMA,
                    "payload": record.to_mapping(),
                }
            )
        )

    _write_jsonl(root / "event.bus.jsonl", (event.to_mapping() for event in events))
    _write_jsonl(root / "context.bus.jsonl", (context.to_mapping() for context in contexts))
    return len(events), len(contexts)


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
            handle.write("\n")
