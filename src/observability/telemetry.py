from __future__ import annotations

from dataclasses import dataclass

from contracts.event import Event
from contracts.policy import Decision
from contracts.telemetry import TelemetrySnapshot


@dataclass(slots=True)
class KernelTelemetry:
    """Collecteur de télémétrie kernel Phase 1.7.

    Cet objet n'est pas un chemin de commande. Il ne publie pas d'événements,
    ne décide rien et ne modifie pas l'exécution. Il mesure uniquement les
    invariants nécessaires avant l'arrivée d'OpenVINO : queue, dispatch,
    refus policy et ticks contexte.
    """

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

    def record_enqueue(self, event: Event, queue_size: int) -> None:
        self.events_enqueued += 1
        self._record_event(event)
        self._record_queue_size(queue_size)

    def record_dequeue(self, event: Event, queue_size: int) -> None:
        self.events_dequeued += 1
        self._record_event(event)
        self._record_queue_size(queue_size)

    def record_dispatch_success(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None:
        self.events_dispatched += 1
        self.total_queue_latency_ns += max(0, queue_latency_ns)
        self.total_dispatch_latency_ns += max(0, dispatch_latency_ns)
        self._record_event(event)
        self._record_queue_size(queue_size)

    def record_dispatch_error(
        self,
        event: Event,
        queue_latency_ns: int,
        dispatch_latency_ns: int,
        queue_size: int,
    ) -> None:
        self.events_failed += 1
        self.total_queue_latency_ns += max(0, queue_latency_ns)
        self.total_dispatch_latency_ns += max(0, dispatch_latency_ns)
        self._record_event(event)
        self._record_queue_size(queue_size)

    def record_policy_denied(
        self,
        event: Event,
        decision: Decision,
        queue_size: int,
    ) -> None:
        self.events_denied += 1
        self.last_denial_rule = decision.rule
        self._record_event(event)
        self._record_queue_size(queue_size)

    def record_context_tick(self, queue_size: int) -> None:
        self.context_ticks += 1
        self._record_queue_size(queue_size)

    def snapshot(self, queue_size: int | None = None) -> TelemetrySnapshot:
        if queue_size is not None:
            self._record_queue_size(queue_size)

        return TelemetrySnapshot(
            events_enqueued=self.events_enqueued,
            events_dequeued=self.events_dequeued,
            events_dispatched=self.events_dispatched,
            events_failed=self.events_failed,
            events_denied=self.events_denied,
            context_ticks=self.context_ticks,
            max_queue_size=self.max_queue_size,
            current_queue_size=self.current_queue_size,
            total_queue_latency_ns=self.total_queue_latency_ns,
            total_dispatch_latency_ns=self.total_dispatch_latency_ns,
            last_event_type=self.last_event_type,
            last_denial_rule=self.last_denial_rule,
        )

    def _record_event(self, event: Event) -> None:
        self.last_event_type = event.type.name

    def _record_queue_size(self, queue_size: int) -> None:
        self.current_queue_size = queue_size
        if queue_size > self.max_queue_size:
            self.max_queue_size = queue_size
