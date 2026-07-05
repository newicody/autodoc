"""Read existing event.bus/context.bus facts for VisPy/browser views.

0093-r2 is deliberately a read adapter for existing runtime objects. It does not
instantiate EventBus, does not create a new bus, and does not build a parallel
observation path. The adapter attaches a read tap to an already-created event
bus through event_bus.subscribe(), drains already-published observable facts, and
projects the current context snapshot source.

Operational intent:

    existing EventBus + existing context source
    -> event_bus.subscribe() read tap
    -> drain_existing_event_bus_reader()
    -> read_existing_bus_visualization_snapshot()
    -> ExistingBusVisualizationSnapshot.to_mapping()

Boundaries deliberately kept out of this module:
- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No kernel loop modification.
- EventBus is observation only.
- Events/bus facts are facts, not commands.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- The adapter reads existing event.bus/context.bus objects.
- The adapter does not instantiate EventBus.
- The adapter does not create a parallel bus.
- No Qdrant.
- No LLM.
- No OpenVINO.
- No network, GitHub API, VisPy dependency, or browser launch.
- stdlib only.
"""

from __future__ import annotations

from asyncio import QueueEmpty
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from queue import Empty
from types import MappingProxyType
from typing import Any, Protocol

from contracts.context import GlobalContextSnapshot
from contracts.event import Event, EventType

BUS_VISUALIZATION_SCHEMA = "missipy.bus_visualization.v1"
BUS_VISUALIZATION_SOURCE = "existing event.bus/context.bus"

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]


class ExistingEventReader(Protocol):
    """Minimal queue contract returned by the existing EventBus."""

    def get_nowait(self) -> Event:
        """Return the next observable event without waiting, or raise when empty."""
        ...

    def empty(self) -> bool:
        """Return whether the read queue is empty."""
        ...


class ExistingEventBus(Protocol):
    """Minimal read-attachment contract of the existing EventBus."""

    def subscribe(self, event_type: EventType | None = None) -> ExistingEventReader:
        """Return a read queue for already-created EventBus observers."""
        ...


class ExistingContextSnapshotSource(Protocol):
    """Minimal contract exposed by the existing context source."""

    last_snapshot: GlobalContextSnapshot | None


@dataclass(frozen=True, slots=True)
class ExistingBusVisualizationTap:
    """Read tap attached to existing event.bus/context.bus objects.

    The tap owns no bus. It only keeps the read queue returned by the already
    instantiated EventBus and a reference to the existing context source.
    """

    event_reader: ExistingEventReader
    context_source: (
        GlobalContextSnapshot
        | Mapping[str, Mapping[str, Any]]
        | ExistingContextSnapshotSource
        | None
    ) = None


@dataclass(frozen=True, slots=True)
class BusEventView:
    """Serializable observable view of one EventBus fact."""

    index: int
    event_id: str
    event_type: str
    source: str
    dest: str
    priority: int
    timestamp_ns: int
    correlation_id: str | None
    has_payload: bool
    metadata: Mapping[str, JsonValue]

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "index": self.index,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "dest": self.dest,
            "priority": self.priority,
            "timestamp_ns": self.timestamp_ns,
            "correlation_id": self.correlation_id,
            "has_payload": self.has_payload,
            "metadata": _thaw_json_value(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextComponentView:
    """Serializable observable view of one component context fact."""

    name: str
    fields: Mapping[str, JsonValue]

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "fields": _thaw_json_value(self.fields),
        }


@dataclass(frozen=True, slots=True)
class ExistingBusVisualizationSnapshot:
    """Stable snapshot for VisPy/browser adapters.

    The snapshot is a representation of observable facts only. It does not
    command components and it does not choose policy.
    """

    schema: str
    source: str
    max_events: int
    events: tuple[BusEventView, ...]
    components: tuple[ContextComponentView, ...]
    event_limit_reached: bool

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def component_count(self) -> int:
        return len(self.components)

    def to_mapping(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "source": self.source,
            "max_events": self.max_events,
            "event_count": self.event_count,
            "component_count": self.component_count,
            "event_limit_reached": self.event_limit_reached,
            "events": tuple(event.to_mapping() for event in self.events),
            "components": tuple(component.to_mapping() for component in self.components),
        }


def attach_existing_bus_visualization_tap(
    event_bus: ExistingEventBus,
    *,
    context_source: (
        GlobalContextSnapshot
        | Mapping[str, Mapping[str, Any]]
        | ExistingContextSnapshotSource
        | None
    ) = None,
    event_type: EventType | None = None,
) -> ExistingBusVisualizationTap:
    """Attach a visualization read tap to the existing EventBus.

    This function calls event_bus.subscribe() on the object supplied by the
    runtime. It does not instantiate EventBus and it does not create a parallel
    bus. The returned tap can be read later by
    read_existing_bus_visualization_snapshot().
    """

    event_reader = event_bus.subscribe(event_type)
    return ExistingBusVisualizationTap(
        event_reader=event_reader,
        context_source=context_source,
    )


def read_existing_bus_visualization_snapshot(
    tap: ExistingBusVisualizationTap,
    *,
    max_events: int = 256,
) -> ExistingBusVisualizationSnapshot:
    """Read a one-shot visualization snapshot from an existing-bus tap."""

    events = drain_existing_event_bus_reader(tap.event_reader, max_events=max_events)
    limit = _validate_max_events(max_events)
    event_limit_reached = len(events) >= limit and not tap.event_reader.empty()
    return build_existing_bus_visualization_snapshot(
        events,
        context_source=tap.context_source,
        max_events=limit,
        event_limit_reached=event_limit_reached,
    )


def drain_existing_event_bus_reader(
    event_reader: ExistingEventReader,
    *,
    max_events: int = 256,
) -> tuple[Event, ...]:
    """Drain at most max_events observable events without waiting.

    This function is intentionally one-shot. It is not a watcher and it does not
    create a task or loop. The caller owns scheduling and authorization.
    """

    limit = _validate_max_events(max_events)
    events: list[Event] = []
    while len(events) < limit:
        try:
            event = event_reader.get_nowait()
        except (Empty, QueueEmpty):
            break
        events.append(event)
        task_done = getattr(event_reader, "task_done", None)
        if callable(task_done):
            task_done()
    return tuple(events)


def build_existing_bus_visualization_snapshot(
    events: Iterable[Event],
    *,
    context_source: (
        GlobalContextSnapshot
        | Mapping[str, Mapping[str, Any]]
        | ExistingContextSnapshotSource
        | None
    ) = None,
    max_events: int = 256,
    event_limit_reached: bool = False,
) -> ExistingBusVisualizationSnapshot:
    """Project existing event.bus/context.bus facts into a stable snapshot."""

    limit = _validate_max_events(max_events)
    selected_events = tuple(events)[:limit]
    context_snapshot = _resolve_existing_context_snapshot(context_source)
    return ExistingBusVisualizationSnapshot(
        schema=BUS_VISUALIZATION_SCHEMA,
        source=BUS_VISUALIZATION_SOURCE,
        max_events=limit,
        events=tuple(_event_to_view(index, event) for index, event in enumerate(selected_events)),
        components=_context_to_views(context_snapshot),
        event_limit_reached=event_limit_reached,
    )


def _resolve_existing_context_snapshot(
    context_source: (
        GlobalContextSnapshot
        | Mapping[str, Mapping[str, Any]]
        | ExistingContextSnapshotSource
        | None
    ),
) -> GlobalContextSnapshot | Mapping[str, Mapping[str, Any]] | None:
    if context_source is None:
        return None
    if isinstance(context_source, GlobalContextSnapshot):
        return context_source
    if isinstance(context_source, Mapping):
        return context_source
    snapshot = getattr(context_source, "last_snapshot", None)
    if snapshot is None:
        return None
    if isinstance(snapshot, GlobalContextSnapshot):
        return snapshot
    if isinstance(snapshot, Mapping):
        return snapshot
    raise TypeError(f"Invalid existing context snapshot: {snapshot!r}")


def _event_to_view(index: int, event: Event) -> BusEventView:
    return BusEventView(
        index=index,
        event_id=event.id,
        event_type=event.type.name,
        source=event.source,
        dest=event.dest,
        priority=event.priority,
        timestamp_ns=event.timestamp_ns,
        correlation_id=event.correlation_id,
        has_payload=event.payload is not None,
        metadata=_freeze_json_mapping(event.metadata),
    )


def _context_to_views(
    context_snapshot: GlobalContextSnapshot | Mapping[str, Mapping[str, Any]] | None,
) -> tuple[ContextComponentView, ...]:
    if context_snapshot is None:
        return ()
    if isinstance(context_snapshot, GlobalContextSnapshot):
        components = context_snapshot.components
    else:
        components = context_snapshot
    return tuple(
        ContextComponentView(name=name, fields=_freeze_json_mapping(fields))
        for name, fields in sorted(components.items())
    )


def _validate_max_events(max_events: int) -> int:
    if isinstance(max_events, bool) or max_events <= 0:
        raise ValueError("max_events must be a positive integer")
    return max_events


def _freeze_json_mapping(data: Mapping[str, Any]) -> Mapping[str, JsonValue]:
    frozen = {str(key): _freeze_json_value(value) for key, value in data.items()}
    return MappingProxyType(frozen)


def _freeze_json_value(value: Any) -> JsonValue:
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _thaw_json_value(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_thaw_json_value(item) for item in value)
    return value
