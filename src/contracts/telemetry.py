from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    """Image immuable de la télémétrie kernel minimale.

    Le snapshot reste une donnée de contrat : il peut être exposé au contexte,
    testé ou sérialisé sans donner accès à l'objet mutable qui collecte les
    compteurs.
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

    @property
    def average_queue_latency_ns(self) -> int:
        """Latence moyenne entre création de l'événement et dispatch."""

        if self.events_dispatched == 0:
            return 0
        return self.total_queue_latency_ns // self.events_dispatched

    @property
    def average_dispatch_latency_ns(self) -> int:
        """Durée moyenne du Dispatcher pour les événements traités."""

        if self.events_dispatched == 0:
            return 0
        return self.total_dispatch_latency_ns // self.events_dispatched
