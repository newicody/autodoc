"""Scheduler intention event emission surface for phase 0250.

This module builds an immutable event envelope from a typed Scheduler intention.
It validates the envelope against the EventBus attribute readiness from phase
0249, but it does not create an EventBus, publish events, call Scheduler.run, or
trigger any runtime action.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from context.prod_server_eventbus_attributes_readiness_0249 import (
    build_eventbus_attributes_readiness,
)


SCHEDULER_INTENTION_EVENT_EMISSION_VERSION = "0250.r1"


SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY: dict[str, bool] = {
    "emission_surface_only": True,
    "uses_eventbus_attribute_readiness": True,
    "creates_eventbus": False,
    "publishes_events": False,
    "calls_scheduler_run": False,
    "dispatches_handler": False,
    "starts_threads": False,
    "writes_postgresql": False,
    "runs_openvino_inference": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class TypedSchedulerIntention:
    """Minimal typed intention that may be observed as an EventBus fact."""

    intent_id: str
    intent_type: str
    component: str
    phase: str
    trace_id: str
    priority: int
    sql_ref: str = ""
    qdrant_ref: str = ""
    github_ref: str = ""
    project_push_frame_ref: str = ""
    payload_hash: str = ""
    secret: str = ""


@dataclass(frozen=True)
class EventEnvelope:
    """Immutable observation envelope derived from a Scheduler intention."""

    event_id: str
    schema_version: str
    event_type: str
    trace_id: str
    component: str
    phase: str
    attributes: dict[str, str | int]
    redacted_attributes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SchedulerIntentionEventIssue:
    """One issue found while deriving an event envelope."""

    field: str
    message: str


@dataclass(frozen=True)
class SchedulerIntentionEventEmissionReport:
    """JSON-compatible report for the derived intention event envelope."""

    version: str
    server_config_path: str
    openvino_config_path: str
    valid: bool
    intention: TypedSchedulerIntention
    envelope: EventEnvelope | None
    issues: tuple[SchedulerIntentionEventIssue, ...]


def sample_scheduler_intention() -> TypedSchedulerIntention:
    """Return a deterministic sample intention for local smoke checks."""

    return TypedSchedulerIntention(
        intent_id="intent:0250:sample-sql-openvino-qdrant-projection",
        intent_type="scheduler.intent.projection.prepare",
        component="scheduler",
        phase="D07_functional_handler_chain",
        trace_id="trace:0250:sample",
        priority=50,
        sql_ref="context_records.id",
        qdrant_ref="autodoc_context_e5_small",
        payload_hash="sha256:sample-content-hash",
    )


def _event_id(intention: TypedSchedulerIntention) -> str:
    seed = "|".join((intention.intent_id, intention.intent_type, intention.trace_id))
    return "event:" + str(uuid5(NAMESPACE_URL, seed))


def _allowed_sets(surface: Any) -> tuple[set[str], set[str], set[str]]:
    required = set(surface.required)
    optional = set(surface.optional)
    redacted = set(surface.optional_redacted)
    return required, optional, redacted


def event_envelope_from_intention(
    intention: TypedSchedulerIntention,
    *,
    server_config_path: Path,
    openvino_config_path: Path,
) -> SchedulerIntentionEventEmissionReport:
    """Build an immutable event envelope from a typed Scheduler intention."""

    readiness = build_eventbus_attributes_readiness(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    issues: list[SchedulerIntentionEventIssue] = []

    if not readiness.ready:
        for issue in readiness.issues:
            issues.append(SchedulerIntentionEventIssue(issue.field, issue.message))

    if readiness.surface is None:
        return SchedulerIntentionEventEmissionReport(
            version=SCHEDULER_INTENTION_EVENT_EMISSION_VERSION,
            server_config_path=str(server_config_path),
            openvino_config_path=str(openvino_config_path),
            valid=False,
            intention=intention,
            envelope=None,
            issues=tuple(issues + [SchedulerIntentionEventIssue("eventbus.attributes", "attribute surface is missing")]),
        )

    required, optional, redacted = _allowed_sets(readiness.surface)
    attributes: dict[str, str | int] = {
        "schema_version": SCHEDULER_INTENTION_EVENT_EMISSION_VERSION,
        "event_type": "scheduler.intention.observed",
        "trace_id": intention.trace_id,
        "component": intention.component,
        "phase": intention.phase,
        "intent_id": intention.intent_id,
        "priority": intention.priority,
    }
    optional_values = {
        "sql_ref": intention.sql_ref,
        "qdrant_ref": intention.qdrant_ref,
        "github_ref": intention.github_ref,
        "project_push_frame_ref": intention.project_push_frame_ref,
        "payload_hash": intention.payload_hash,
        "secret": intention.secret,
    }
    for key, value in optional_values.items():
        if value:
            if key in redacted:
                attributes[key] = "<redacted>"
            elif key in optional or key in required:
                attributes[key] = value
            else:
                issues.append(SchedulerIntentionEventIssue(key, "attribute is not allowlisted"))

    for key in required:
        if key not in attributes:
            issues.append(SchedulerIntentionEventIssue(key, "missing required event attribute"))

    if "payload" in attributes or "payload_json" in attributes:
        issues.append(SchedulerIntentionEventIssue("payload", "large payloads are forbidden in EventBus envelopes"))

    envelope = EventEnvelope(
        event_id=_event_id(intention),
        schema_version=SCHEDULER_INTENTION_EVENT_EMISSION_VERSION,
        event_type="scheduler.intention.observed",
        trace_id=intention.trace_id,
        component=intention.component,
        phase=intention.phase,
        attributes=attributes,
        redacted_attributes=tuple(sorted(redacted & set(attributes))),
    )

    return SchedulerIntentionEventEmissionReport(
        version=SCHEDULER_INTENTION_EVENT_EMISSION_VERSION,
        server_config_path=str(server_config_path),
        openvino_config_path=str(openvino_config_path),
        valid=not issues,
        intention=replace(intention, secret="<redacted>" if intention.secret else ""),
        envelope=envelope,
        issues=tuple(issues),
    )


def scheduler_intention_event_emission_to_dict(report: SchedulerIntentionEventEmissionReport) -> dict[str, Any]:
    """Convert a Scheduler intention event report to JSON-compatible data."""

    return asdict(report)


def write_scheduler_intention_event_emission_report(*, server_config_path: Path, openvino_config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the sample Scheduler intention event envelope report."""

    report = event_envelope_from_intention(
        sample_scheduler_intention(),
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
    )
    payload = {
        "production_server_scheduler_intention_event_emission_written": True,
        "scheduler_intention_event_emission": scheduler_intention_event_emission_to_dict(report),
        "boundary": dict(SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
