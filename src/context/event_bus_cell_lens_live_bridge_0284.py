from __future__ import annotations

import asyncio
import math
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from context.cell_observation_event import CellObservationEvent
from context.cell_snapshot import CELL_LIFECYCLE_STATES
from context.cell_snapshot_journal import CellSnapshotJournalWriter
from contracts.event import Event, EventType


Clock = Callable[[], str]


class EventBusSubscriber(Protocol):
    def subscribe(self, event_type: EventType | None = None) -> asyncio.Queue[Event]: ...


@dataclass(frozen=True, slots=True)
class EventBusCellLensLiveBridgeStats:
    """Passive bridge counters exposed for diagnostics and tests."""

    observed_count: int
    written_count: int
    dropped_count: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors and self.dropped_count == 0


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _metadata(event: Event) -> Mapping[str, Any]:
    metadata = event.metadata
    return metadata if isinstance(metadata, Mapping) else {}


def _text(metadata: Mapping[str, Any], *names: str) -> str:
    for name in names:
        value = metadata.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _number(metadata: Mapping[str, Any], name: str, default: float) -> float:
    value = metadata.get(name, default)
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def event_lifecycle_state(event: Event) -> str:
    metadata = _metadata(event)
    explicit = _text(metadata, "lifecycle_state", "state")
    if explicit in CELL_LIFECYCLE_STATES:
        return explicit

    if event.type in {EventType.ERROR, EventType.POLICY_DENIED}:
        return "failed"
    if event.type is EventType.SHUTDOWN:
        return "cancelled"
    if event.type is EventType.LOAD:
        return "created"
    if event.type in {
        EventType.CONTEXT_REQUEST,
        EventType.INFERENCE_REQUEST,
        EventType.SOURCE_CANDIDATE_INTAKE,
        EventType.SOURCE_CANDIDATE_REVIEW,
        EventType.SOURCE_CANDIDATE_DECISION,
    }:
        return "queued"
    if event.type in {EventType.START, EventType.TICK}:
        return "running"
    return "completed"


def event_to_cell_observation_event(event: Event, *, observed_at: str) -> CellObservationEvent:
    """Project one EventBus event into the existing immutable Cell Lens contract."""

    metadata = _metadata(event)
    lifecycle_state = event_lifecycle_state(event)
    source_task_id = _text(metadata, "source_task_id", "task_id") or str(
        event.correlation_id or ""
    )
    source_component_id = _text(metadata, "source_component_id", "component_id") or str(
        event.source
    )
    portable_ref = _text(
        metadata,
        "cell_id",
        "specialist_ref",
        "laboratory_ref",
        "visit_ref",
        "route_ref",
        "sql_ref",
        "qdrant_ref",
    )
    cell_id = portable_ref or (
        f"task:{source_task_id}" if source_task_id else f"component:{source_component_id}"
    )
    source_class = _text(metadata, "source_class", "cell_kind") or str(event.source)

    return CellObservationEvent(
        event_id=str(event.id),
        event_type=f"task.{lifecycle_state}",
        source_class=source_class,
        observed_at=observed_at,
        score=_number(metadata, "score", float(event.priority)),
        age=max(0.0, _number(metadata, "age", 0.0)),
        cost=max(0.0, _number(metadata, "cost", 0.0)),
        cell_id=cell_id,
        source_task_id=source_task_id,
        source_component_id=source_component_id,
        lifecycle_state=lifecycle_state,
    )


class EventBusCellLensLiveBridge:
    """Observe the real EventBus and append Cell Lens snapshots without control effects."""

    def __init__(
        self,
        event_bus: EventBusSubscriber,
        journal_path: Path,
        *,
        clock: Clock = utc_now_text,
    ) -> None:
        self._event_bus = event_bus
        self._writer = CellSnapshotJournalWriter(Path(journal_path))
        self._clock = clock
        self._queue: asyncio.Queue[Event] | None = None
        self._task: asyncio.Task[None] | None = None
        self._observed_count = 0
        self._written_count = 0
        self._dropped_count = 0
        self._errors: list[str] = []

    @property
    def journal_path(self) -> Path:
        return self._writer.path

    @property
    def stats(self) -> EventBusCellLensLiveBridgeStats:
        return EventBusCellLensLiveBridgeStats(
            observed_count=self._observed_count,
            written_count=self._written_count,
            dropped_count=self._dropped_count,
            errors=tuple(self._errors),
        )

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._queue = self._event_bus.subscribe(None)
        self._task = asyncio.create_task(
            self._consume(),
            name="missipy-eventbus-cell-lens-live-bridge",
        )

    async def flush(self) -> None:
        if self._queue is not None:
            await self._queue.join()

    async def stop(self) -> None:
        task = self._task
        if task is None:
            return
        await self.flush()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        self._task = None

    async def _consume(self) -> None:
        if self._queue is None:
            raise RuntimeError("bridge queue is not initialized")
        while True:
            event = await self._queue.get()
            self._observed_count += 1
            try:
                observation = event_to_cell_observation_event(
                    event,
                    observed_at=self._clock(),
                )
                result = await asyncio.to_thread(
                    self._writer.append,
                    observation.to_cell_snapshot(),
                )
                self._written_count += result.written_count
                self._dropped_count += result.dropped_count
                self._errors.extend(result.errors)
            except Exception as exc:  # passive observer must not affect the producer
                self._dropped_count += 1
                self._errors.append(f"{type(exc).__name__}: {exc}")
            finally:
                self._queue.task_done()
