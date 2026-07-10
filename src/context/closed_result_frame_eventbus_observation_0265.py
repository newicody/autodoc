"""EventBus observation facts for the closed ResultFrame.

0265 attaches observation-only EventBus facts to the 0264 closed ResultFrame.
Events are immutable facts.  They carry no Request, do not ask for replies, and
must not be interpreted as commands.

Boundary:
- EventBus is observation only.
- Events are facts, not commands.
- 0265 does not execute SQL, OpenVINO, or Qdrant.
- Scheduler.run is not modified.
- No RuntimeManager is introduced.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field, is_dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from contracts.event import Event, EventType
from kernel.event_bus import EventBus


OBSERVATION_SCHEMA = "missipy.closed_result_frame_eventbus_observation.v1"
OBSERVATION_SOURCE = "scheduler-managed-closed-result-frame-0265"
OBSERVATION_DEST = "observability"
OBSERVATION_EVENT_TYPE = EventType.INFERENCE_RESULT


@dataclass(frozen=True)
class ClosedResultFrameObservationFact:
    """Serializable observation fact derived from the closed ResultFrame."""

    fact_ref: str
    fact_kind: str
    payload: Mapping[str, Any]
    source_frame_schema: str = "missipy.scheduler_managed_closed_result_frame.v1"
    observation_only: bool = True
    command: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "fact_ref": self.fact_ref,
            "fact_kind": self.fact_kind,
            "payload": dict(self.payload),
            "source_frame_schema": self.source_frame_schema,
            "observation_only": self.observation_only,
            "command": self.command,
        }


@dataclass(frozen=True)
class ClosedResultFrameEventBusObservationReport:
    """Report produced from closed frame observation facts."""

    valid: bool
    issues: tuple[str, ...]
    frame_ref: str
    facts: tuple[ClosedResultFrameObservationFact, ...] = field(default_factory=tuple)
    published_count: int = 0
    observed_count: int = 0
    event_ids: tuple[str, ...] = ()
    event_types: tuple[str, ...] = ()
    scheduler_owned: bool = True
    eventbus_observation_only: bool = True
    events_are_facts_not_commands: bool = True
    executes_runtime: bool = False
    starts_postgresql: bool = False
    starts_openvino: bool = False
    starts_qdrant: bool = False
    modifies_scheduler_run: bool = False
    creates_runtime_manager: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": OBSERVATION_SCHEMA,
            "closed_result_frame_eventbus_observation": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "frame_ref": self.frame_ref,
            "fact_count": len(self.facts),
            "facts": [fact.to_mapping() for fact in self.facts],
            "published_count": self.published_count,
            "observed_count": self.observed_count,
            "event_ids": list(self.event_ids),
            "event_types": list(self.event_types),
            "scheduler_owned": self.scheduler_owned,
            "eventbus_observation_only": self.eventbus_observation_only,
            "events_are_facts_not_commands": self.events_are_facts_not_commands,
            "executes_runtime": self.executes_runtime,
            "starts_postgresql": self.starts_postgresql,
            "starts_openvino": self.starts_openvino,
            "starts_qdrant": self.starts_qdrant,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "creates_runtime_manager": self.creates_runtime_manager,
        }


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "to_mapping") and callable(value.to_mapping):
        payload = value.to_mapping()
        if isinstance(payload, Mapping):
            return payload
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def validate_closed_result_frame_for_observation(frame: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate that the frame is safe to expose as observation facts."""

    issues: list[str] = []
    if frame.get("valid") is not True:
        issues.append("closed ResultFrame must be valid")
    sql_ref = str(frame.get("sql_ref") or "")
    if not sql_ref.startswith("sql:"):
        issues.append("closed ResultFrame must expose a typed sql_ref")
    embedding_ref = str(frame.get("embedding_ref") or "")
    if not embedding_ref.startswith("embedding:"):
        issues.append("closed ResultFrame must expose a typed embedding_ref")
    if frame.get("executes_runtime") is not False:
        issues.append("closed ResultFrame observation must be non-runtime")
    if frame.get("starts_openvino") is not False:
        issues.append("closed ResultFrame observation must not start OpenVINO")
    if frame.get("starts_qdrant") is not False:
        issues.append("closed ResultFrame observation must not start Qdrant")
    if frame.get("starts_postgresql") is not False:
        issues.append("closed ResultFrame observation must not start PostgreSQL")
    if frame.get("modifies_scheduler_run") is not False:
        issues.append("closed ResultFrame observation must not modify Scheduler.run")
    return tuple(issues)


def build_closed_result_frame_observation_facts(
    frame: Mapping[str, Any],
    *,
    frame_ref: str,
) -> tuple[ClosedResultFrameObservationFact, ...]:
    """Build immutable observation facts from the closed frame."""

    sql_ref = str(frame.get("sql_ref") or "")
    embedding_ref = str(frame.get("embedding_ref") or "")
    trace = _mapping(frame.get("trace", {}))

    return (
        ClosedResultFrameObservationFact(
            fact_ref=f"event-fact:0265:{sql_ref}:closed",
            fact_kind="closed_result_frame.validated",
            payload={
                "frame_ref": frame_ref,
                "sql_ref": sql_ref,
                "embedding_ref": embedding_ref,
                "projection_point_count": frame.get("projection_point_count", 0),
                "recall_hit_count": frame.get("recall_hit_count", 0),
                "hydrated_count": frame.get("hydrated_count", 0),
                "missing_count": frame.get("missing_count", 0),
            },
        ),
        ClosedResultFrameObservationFact(
            fact_ref=f"event-fact:0265:{sql_ref}:authority",
            fact_kind="closed_result_frame.authority_boundary",
            payload={
                "frame_ref": frame_ref,
                "sql_ref": sql_ref,
                "sql_remains_authority": frame.get("sql_remains_authority", True),
                "qdrant_projection_recall_refs_only": frame.get(
                    "qdrant_projection_recall_refs_only",
                    True,
                ),
                "openvino_already_executed_by_0261": frame.get(
                    "openvino_already_executed_by_0261",
                    True,
                ),
            },
        ),
        ClosedResultFrameObservationFact(
            fact_ref=f"event-fact:0265:{sql_ref}:trace",
            fact_kind="closed_result_frame.trace_summary",
            payload={
                "frame_ref": frame_ref,
                "sql_ref": sql_ref,
                "trace_steps": tuple(str(step) for step in trace.keys()),
            },
        ),
    )


def observation_fact_to_event(fact: ClosedResultFrameObservationFact) -> Event:
    """Convert an observation fact into an EventBus event.

    The event has no Request and no reply channel.  It is a fact-only
    observation and must not be routed as a command.
    """

    payload = fact.to_mapping()
    return Event(
        type=OBSERVATION_EVENT_TYPE,
        source=OBSERVATION_SOURCE,
        dest=OBSERVATION_DEST,
        payload=payload,
        priority=0,
        correlation_id=fact.fact_ref,
        request=None,
        metadata=MappingProxyType(
            {
                "schema": OBSERVATION_SCHEMA,
                "observation_only": True,
                "command": False,
                "fact_kind": fact.fact_kind,
            }
        ),
    )


def build_closed_result_frame_eventbus_observation_report(
    frame: Mapping[str, Any],
    *,
    frame_ref: str,
) -> ClosedResultFrameEventBusObservationReport:
    """Build an observation report without publishing to EventBus."""

    issues = validate_closed_result_frame_for_observation(frame)
    facts: tuple[ClosedResultFrameObservationFact, ...] = ()
    if not issues:
        facts = build_closed_result_frame_observation_facts(frame, frame_ref=frame_ref)
    return ClosedResultFrameEventBusObservationReport(
        valid=not issues,
        issues=issues,
        frame_ref=frame_ref,
        facts=facts,
    )


async def publish_closed_result_frame_observation_facts(
    event_bus: EventBus,
    facts: Sequence[ClosedResultFrameObservationFact],
) -> tuple[Event, ...]:
    """Publish fact-only events to an existing EventBus."""

    published: list[Event] = []
    for fact in facts:
        event = observation_fact_to_event(fact)
        await event_bus.publish(event)
        published.append(event)
    return tuple(published)


async def publish_and_observe_closed_result_frame_facts(
    facts: Sequence[ClosedResultFrameObservationFact],
) -> tuple[tuple[Event, ...], tuple[Event, ...]]:
    """Demo publish through an in-memory EventBus and drain observer queue."""

    event_bus = EventBus()
    observer_queue = event_bus.subscribe()
    published = await publish_closed_result_frame_observation_facts(event_bus, facts)

    observed: list[Event] = []
    while not observer_queue.empty():
        observed.append(observer_queue.get_nowait())
    return published, tuple(observed)


def build_and_optionally_publish_closed_result_frame_eventbus_observation(
    frame: Mapping[str, Any],
    *,
    frame_ref: str,
    publish_demo: bool = False,
) -> ClosedResultFrameEventBusObservationReport:
    """Build observation facts and optionally publish them to an in-memory bus."""

    report = build_closed_result_frame_eventbus_observation_report(frame, frame_ref=frame_ref)
    if not report.valid or not publish_demo:
        return report

    published, observed = asyncio.run(publish_and_observe_closed_result_frame_facts(report.facts))
    return ClosedResultFrameEventBusObservationReport(
        valid=True,
        issues=(),
        frame_ref=frame_ref,
        facts=report.facts,
        published_count=len(published),
        observed_count=len(observed),
        event_ids=tuple(event.id for event in published),
        event_types=tuple(event.type.name for event in published),
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def write_report(output: Path, payload: Mapping[str, Any]) -> None:
    """Write a JSON report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
