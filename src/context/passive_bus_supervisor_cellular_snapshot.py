"""Passive bus supervisor cellular snapshot contracts.

This module is intentionally data-only. It converts already-emitted bus events
into a compact cellular snapshot for human supervision surfaces. It is not a bus
producer, not a scheduler adapter, not a policy authority, and not a writer for
SQL, Qdrant, GitHub, SHM, or proxy control planes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import json



CELL_KINDS = frozenset(
    {
        "SCHEDULER",
        "EVENT_BUS",
        "GITHUB_ACTION",
        "GITHUB_ARTIFACT",
        "LOCAL_FETCHER",
        "SOURCE_CANDIDATE",
        "SQL_AUTHORITY",
        "QDRANT_PROJECTION",
        "REHYDRATE",
        "RESPONSE_ARTIFACT",
        "ROUTEPROXY",
        "CONTROLPROXY",
        "SHM_RING",
        "POLICY_GATE",
        "PUSHBACK",
        "UNKNOWN",
    }
)

CELL_STATES = frozenset(
    {
        "idle",
        "queued",
        "running",
        "success",
        "failed",
        "blocked",
        "waiting_policy",
        "draining",
        "stale",
        "unknown",
    }
)

AUTHORITY_BOUNDARY = {
    "observation_only": True,
    "allows_scheduler_run": False,
    "allows_sql_write": False,
    "allows_qdrant_write": False,
    "allows_github_mutation": False,
    "allows_proxy_control": False,
    "allows_policy_decision": False,
    "requires_non_stdlib": False,
}


def _as_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _as_string_mapping(value: Mapping[str, Any] | None) -> dict[str, str]:
    if not value:
        return {}
    return {str(key): _as_string(item) for key, item in value.items()}


def _normalize_cell_kind(value: Any) -> str:
    cell_kind = _as_string(value).strip().upper() or "UNKNOWN"
    if cell_kind not in CELL_KINDS:
        return "UNKNOWN"
    return cell_kind


def _normalize_state(value: Any) -> str:
    state = _as_string(value).strip().lower() or "unknown"
    if state not in CELL_STATES:
        return "unknown"
    return state


def _health_for_state(state: str) -> str:
    if state == "failed":
        return "failed"
    if state == "blocked":
        return "blocked"
    if state == "stale":
        return "stale"
    if state == "waiting_policy":
        return "waiting_policy"
    if state in {"queued", "running", "draining"}:
        return "active"
    if state in {"idle", "success"}:
        return "healthy"
    return "unknown"


@dataclass(frozen=True)
class BusSupervisorEvent:
    """One already-observed event from the passive bus surface."""

    event_id: str
    event_kind: str
    cell_id: str
    cell_kind: str
    state: str
    observed_at: str
    source_ref: str = ""
    route_ref: str = ""
    policy_decision_id: str = ""
    artifact_ref: str = ""
    sql_ref: str = ""
    qdrant_ref: str = ""
    shm_ref: str = ""
    error: str = ""
    payload: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_id", _as_string(self.event_id))
        object.__setattr__(self, "event_kind", _as_string(self.event_kind))
        object.__setattr__(self, "cell_id", _as_string(self.cell_id))
        object.__setattr__(self, "cell_kind", _normalize_cell_kind(self.cell_kind))
        object.__setattr__(self, "state", _normalize_state(self.state))
        object.__setattr__(self, "observed_at", _as_string(self.observed_at))
        object.__setattr__(self, "source_ref", _as_string(self.source_ref))
        object.__setattr__(self, "route_ref", _as_string(self.route_ref))
        object.__setattr__(
            self, "policy_decision_id", _as_string(self.policy_decision_id)
        )
        object.__setattr__(self, "artifact_ref", _as_string(self.artifact_ref))
        object.__setattr__(self, "sql_ref", _as_string(self.sql_ref))
        object.__setattr__(self, "qdrant_ref", _as_string(self.qdrant_ref))
        object.__setattr__(self, "shm_ref", _as_string(self.shm_ref))
        object.__setattr__(self, "error", _as_string(self.error))
        object.__setattr__(self, "payload", _as_string_mapping(self.payload))
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.event_kind:
            raise ValueError("event_kind is required")
        if not self.cell_id:
            raise ValueError("cell_id is required")
        if not self.observed_at:
            raise ValueError("observed_at is required")

    def refs(self) -> dict[str, str]:
        refs = {
            "source_ref": self.source_ref,
            "route_ref": self.route_ref,
            "policy_decision_id": self.policy_decision_id,
            "artifact_ref": self.artifact_ref,
            "sql_ref": self.sql_ref,
            "qdrant_ref": self.qdrant_ref,
            "shm_ref": self.shm_ref,
        }
        return {key: value for key, value in refs.items() if value}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "cell_id": self.cell_id,
            "cell_kind": self.cell_kind,
            "state": self.state,
            "observed_at": self.observed_at,
            "source_ref": self.source_ref,
            "route_ref": self.route_ref,
            "policy_decision_id": self.policy_decision_id,
            "artifact_ref": self.artifact_ref,
            "sql_ref": self.sql_ref,
            "qdrant_ref": self.qdrant_ref,
            "shm_ref": self.shm_ref,
            "error": self.error,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class CellularBusCell:
    """Current passive-supervision view of one runtime cell."""

    cell_id: str
    cell_kind: str
    state: str
    health: str
    last_event_id: str
    last_event_kind: str
    last_seen_at: str
    refs: Mapping[str, str] = field(default_factory=dict)
    error: str = ""
    event_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "cell_kind": self.cell_kind,
            "state": self.state,
            "health": self.health,
            "last_event_id": self.last_event_id,
            "last_event_kind": self.last_event_kind,
            "last_seen_at": self.last_seen_at,
            "refs": dict(self.refs),
            "error": self.error,
            "event_count": self.event_count,
        }


@dataclass(frozen=True)
class PassiveBusSupervisorSnapshot:
    """Deterministic cellular snapshot derived from passive bus events."""

    generated_at: str
    cells: tuple[CellularBusCell, ...]
    event_count: int
    blocked_count: int
    failed_count: int
    stale_count: int
    authority_boundary: Mapping[str, bool] = field(
        default_factory=lambda: dict(AUTHORITY_BOUNDARY)
    )
    metadata: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "event_count": self.event_count,
            "cell_count": len(self.cells),
            "blocked_count": self.blocked_count,
            "failed_count": self.failed_count,
            "stale_count": self.stale_count,
            "authority_boundary": dict(self.authority_boundary),
            "metadata": dict(self.metadata),
            "cells": [cell.to_dict() for cell in self.cells],
        }


def event_from_mapping(mapping: Mapping[str, Any]) -> BusSupervisorEvent:
    """Build a normalized event from a JSON-compatible mapping."""

    return BusSupervisorEvent(
        event_id=mapping.get("event_id", ""),
        event_kind=mapping.get("event_kind", ""),
        cell_id=mapping.get("cell_id", ""),
        cell_kind=mapping.get("cell_kind", "UNKNOWN"),
        state=mapping.get("state", "unknown"),
        observed_at=mapping.get("observed_at", ""),
        source_ref=mapping.get("source_ref", ""),
        route_ref=mapping.get("route_ref", ""),
        policy_decision_id=mapping.get("policy_decision_id", ""),
        artifact_ref=mapping.get("artifact_ref", ""),
        sql_ref=mapping.get("sql_ref", ""),
        qdrant_ref=mapping.get("qdrant_ref", ""),
        shm_ref=mapping.get("shm_ref", ""),
        error=mapping.get("error", ""),
        payload=mapping.get("payload", {}),
    )



def scheduler_supervision_event(
    *,
    event_id: str,
    event_kind: str,
    scheduler_ref: str,
    state: str,
    observed_at: str,
    handler_ref: str = "",
    route_ref: str = "",
    policy_decision_id: str = "",
    artifact_ref: str = "",
    sql_ref: str = "",
    qdrant_ref: str = "",
    shm_ref: str = "",
    error: str = "",
    payload: Mapping[str, Any] | None = None,
) -> BusSupervisorEvent:
    """Create a canonical scheduler supervision event for EventBus emission.

    The returned object is data-only and can be published by the existing
    scheduler/EventBus path or accepted by :class:`PassiveSupervisorSink` in
    tests. This helper does not depend on Scheduler implementation, does not call Scheduler.run,
    and does not dispatch handlers.
    """

    scheduler_name = _as_string(scheduler_ref).strip()
    handler_name = _as_string(handler_ref).strip()
    extra_payload = dict(_as_string_mapping(payload))
    if handler_name:
        extra_payload.setdefault("handler_ref", handler_name)

    cell_id = f"scheduler:{scheduler_name}" if scheduler_name else "scheduler"
    return BusSupervisorEvent(
        event_id=event_id,
        event_kind=event_kind,
        cell_id=cell_id,
        cell_kind="SCHEDULER",
        state=state,
        observed_at=observed_at,
        source_ref=f"scheduler:{scheduler_name}" if scheduler_name else "scheduler",
        route_ref=route_ref,
        policy_decision_id=policy_decision_id,
        artifact_ref=artifact_ref,
        sql_ref=sql_ref,
        qdrant_ref=qdrant_ref,
        shm_ref=shm_ref,
        error=error,
        payload=extra_payload,
    )


def build_cellular_snapshot(
    events: Iterable[BusSupervisorEvent],
    *,
    generated_at: str,
    metadata: Mapping[str, Any] | None = None,
) -> PassiveBusSupervisorSnapshot:
    """Collapse passive bus events into the latest state for each cell."""

    event_list = tuple(events)
    cell_event_counts: dict[str, int] = {}
    latest_by_cell: dict[str, BusSupervisorEvent] = {}

    for event in event_list:
        cell_event_counts[event.cell_id] = cell_event_counts.get(event.cell_id, 0) + 1
        latest_by_cell[event.cell_id] = event

    cells = []
    for cell_id in sorted(latest_by_cell):
        event = latest_by_cell[cell_id]
        cells.append(
            CellularBusCell(
                cell_id=event.cell_id,
                cell_kind=event.cell_kind,
                state=event.state,
                health=_health_for_state(event.state),
                last_event_id=event.event_id,
                last_event_kind=event.event_kind,
                last_seen_at=event.observed_at,
                refs=event.refs(),
                error=event.error,
                event_count=cell_event_counts[event.cell_id],
            )
        )

    return PassiveBusSupervisorSnapshot(
        generated_at=_as_string(generated_at),
        cells=tuple(cells),
        event_count=len(event_list),
        blocked_count=sum(1 for cell in cells if cell.state == "blocked"),
        failed_count=sum(1 for cell in cells if cell.state == "failed"),
        stale_count=sum(1 for cell in cells if cell.state == "stale"),
        metadata=_as_string_mapping(metadata),
    )


class PassiveSupervisorSink:
    """Downstream-only sink for canonical EventBus supervision events.

    The scheduler remains the orchestration authority and an upstream EventBus
    emitter. This sink only accepts events that have already reached the bus. It
    keeps an in-memory cellular projection and can optionally write audit JSONL
    records for replay/debug. Audit output is not part of the hot path.
    """

    def __init__(
        self,
        *,
        metadata: Mapping[str, Any] | None = None,
        audit_jsonl: Path | None = None,
    ) -> None:
        self._events: list[BusSupervisorEvent] = []
        self._metadata = _as_string_mapping(metadata)
        self._audit_jsonl = audit_jsonl

    def accept(
        self,
        event: BusSupervisorEvent | Mapping[str, Any],
    ) -> BusSupervisorEvent:
        """Accept one canonical EventBus event without controlling its source."""

        normalized = event if isinstance(event, BusSupervisorEvent) else event_from_mapping(event)
        self._events.append(normalized)
        if self._audit_jsonl is not None:
            self._write_audit_event(normalized)
        return normalized

    def accept_scheduler_event(
        self,
        *,
        event_id: str,
        event_kind: str,
        scheduler_ref: str,
        state: str,
        observed_at: str,
        handler_ref: str = "",
        route_ref: str = "",
        policy_decision_id: str = "",
        artifact_ref: str = "",
        sql_ref: str = "",
        qdrant_ref: str = "",
        shm_ref: str = "",
        error: str = "",
        payload: Mapping[str, Any] | None = None,
    ) -> BusSupervisorEvent:
        """Accept an upstream Scheduler EventBus event without scheduler control."""

        return self.accept(
            scheduler_supervision_event(
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
        )

    def event_count(self) -> int:
        return len(self._events)

    def events(self) -> tuple[BusSupervisorEvent, ...]:
        return tuple(self._events)

    def snapshot(
        self,
        *,
        generated_at: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> PassiveBusSupervisorSnapshot:
        merged_metadata = dict(self._metadata)
        merged_metadata.update(_as_string_mapping(metadata))
        merged_metadata.setdefault("source", "eventbus_passive_supervisor_sink")
        merged_metadata.setdefault("scheduler_role", "upstream_orchestration_authority")
        merged_metadata.setdefault("eventbus_role", "canonical_runtime_event_transport")
        if self._audit_jsonl is not None:
            merged_metadata.setdefault("audit_jsonl", str(self._audit_jsonl))
        return build_cellular_snapshot(
            self._events,
            generated_at=generated_at,
            metadata=merged_metadata,
        )

    def snapshot_payload(
        self,
        *,
        generated_at: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.snapshot(generated_at=generated_at, metadata=metadata).to_dict()
        payload["cellular_snapshot_written"] = False
        payload["audit_journal_enabled"] = self._audit_jsonl is not None
        payload["supervision_authority_violation"] = False
        return payload

    def write_snapshot(
        self,
        path: Path,
        *,
        generated_at: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.snapshot_payload(generated_at=generated_at, metadata=metadata)
        payload["cellular_snapshot_written"] = True
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload

    def _write_audit_event(self, event: BusSupervisorEvent) -> None:
        if self._audit_jsonl is None:
            return
        self._audit_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with self._audit_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
