from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from contracts.event import Event, EventType
from contracts.inference import InferenceRequest
from contracts.policy import Decision


def _default_destinations() -> frozenset[str]:
    return frozenset(
        {
            "scheduler",
            "context",
            "context.collector",
            "inference",
            "lifecycle",
        }
    )


def _default_inference_models() -> frozenset[str]:
    return frozenset({"dummy"})


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    """Configuration immuable du PolicyEngine minimal.

    Cette configuration reste volontairement simple : elle protège seulement les
    invariants du micro-kernel, sans introduire de logique métier.
    """

    min_priority: int = -1_000
    max_priority: int = 1_000_000
    allowed_destinations: frozenset[str] = field(default_factory=_default_destinations)
    allowed_inference_models: frozenset[str] = field(default_factory=_default_inference_models)
    allow_registered_component_destinations: bool = True


class PolicyEngine:
    """Barrière d'autorisation minimale avant l'entrée en queue.

    Le Scheduler délègue ici la validation des événements. La politique vérifie
    uniquement des invariants de kernel : source, priorité, destination,
    shutdown et backend d'inférence déclaré.
    """

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def decide(
        self,
        event: Event,
        registered_components: Iterable[str] = (),
    ) -> Decision:
        """Retourne une décision déterministe pour l'événement fourni."""

        if not event.source:
            return Decision.deny("event source is required", "event.source.required")

        if event.priority < self.config.min_priority:
            return Decision.deny(
                f"priority {event.priority} is lower than {self.config.min_priority}",
                "event.priority.too_low",
            )

        if event.priority > self.config.max_priority:
            return Decision.deny(
                f"priority {event.priority} is higher than {self.config.max_priority}",
                "event.priority.too_high",
            )

        if event.type is EventType.SHUTDOWN and event.source != "kernel":
            return Decision.deny("only kernel can request shutdown", "shutdown.source.kernel_only")

        destination_decision = self._decide_destination(event, registered_components)
        if not destination_decision.allowed:
            return destination_decision

        if event.type is EventType.INFERENCE_REQUEST:
            return self._decide_inference(event)

        return Decision.allow()

    def _decide_destination(
        self,
        event: Event,
        registered_components: Iterable[str],
    ) -> Decision:
        if event.dest in self.config.allowed_destinations:
            return Decision.allow(rule="event.destination.kernel")

        if self.config.allow_registered_component_destinations:
            if event.dest in frozenset(registered_components):
                return Decision.allow(rule="event.destination.component")

        return Decision.deny(
            f"destination {event.dest!r} is not allowed",
            "event.destination.denied",
        )

    def _decide_inference(self, event: Event) -> Decision:
        if not isinstance(event.payload, InferenceRequest):
            return Decision.deny(
                "INFERENCE_REQUEST payload must be InferenceRequest",
                "inference.payload.type",
            )

        if event.payload.model not in self.config.allowed_inference_models:
            return Decision.deny(
                f"inference model {event.payload.model!r} is not allowed",
                "inference.model.denied",
            )

        return Decision.allow(rule="inference.model.allowed")
