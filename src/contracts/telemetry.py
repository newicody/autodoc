from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts.event import Event
from contracts.policy import Decision


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    """Image immuable de la télémétrie kernel minimale."""

    events_enqueued: int = 0
    events_dequeued: int = 0
    events_dispatched: int = 0
    events_failed: int = 0
    events_denied: int = 0
    context_ticks: int = 0
    max_queue_size: int = 0
    current_queue_size: int = 0
    total_queue_latency_ns: int = 0
    total_dispatch_latency_ns: int = 0
    last_event_type: str | None = None
    last_denial_rule: str | None = None

    @property
    def average_queue_latency_ns(self) -> int:
        if self.events_dispatched == 0:
            return 0
        return self.total_queue_latency_ns // self.events_dispatched

    @property
    def average_dispatch_latency_ns(self) -> int:
        if self.events_dispatched == 0:
            return 0
        return self.total_dispatch_latency_ns // self.events_dispatched


class TelemetryRecorder(Protocol):
    def record_enqueue(self, event: Event, queue_size: int) -> None: ...

    def record_dequeue(self, event: Event, queue_size: int) -> None: ...

    def record_dispatch_success(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None: ...

    def record_dispatch_error(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None: ...

    def record_policy_denied(
        self,
        event: Event,
        decision: Decision,
        queue_size: int,
    ) -> None: ...

    def record_context_tick(self, queue_size: int) -> None: ...

    def snapshot(self, queue_size: int | None = None) -> TelemetrySnapshot: ...


class NullTelemetry:
    def record_enqueue(self, event: Event, queue_size: int) -> None:
        return None

    def record_dequeue(self, event: Event, queue_size: int) -> None:
        return None

    def record_dispatch_success(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None:
        return None

    def record_dispatch_error(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None:
        return None

    def record_policy_denied(
        self,
        event: Event,
        decision: Decision,
        queue_size: int,
    ) -> None:
        return None

    def record_context_tick(self, queue_size: int) -> None:
        return None

    def snapshot(self, queue_size: int | None = None) -> TelemetrySnapshot:
        return TelemetrySnapshot(current_queue_size=queue_size or 0)
