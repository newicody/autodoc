from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from contracts.replay import (
    ReplayEvent,
    ReplayPlan,
    ReplaySandboxResult,
    ReplaySandboxStep,
)

ReplaySandboxHandler = Callable[[ReplayEvent], Any]


def _default_denied_types() -> frozenset[str]:
    return frozenset({"SHUTDOWN"})


@dataclass(frozen=True, slots=True)
class ReplaySandboxConfig:
    """Configuration immuable du sandbox de replay.

    Le sandbox est volontairement fermé par défaut sur les opérations qui
    peuvent ressembler à du contrôle kernel. Il accepte le plan comme trace de
    simulation, mais refuse ``SHUTDOWN`` tant que le replay n'est pas relié à un
    environnement de test explicitement construit.
    """

    max_events: int = 1_000
    allowed_types: frozenset[str] | None = None
    denied_types: frozenset[str] = field(default_factory=_default_denied_types)

    def __post_init__(self) -> None:
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")


class ReplaySandbox:
    """Moteur de replay isolé et déterministe.

    Le ReplaySandbox ne connaît pas le Scheduler, ne publie aucun Event et ne
    reconstruit jamais de Request. Il rejoue un ReplayPlan dans une table de
    handlers de simulation synchrones, afin de tester l'ordre et les invariants
    sans affecter le kernel de production.
    """

    def __init__(
        self,
        config: ReplaySandboxConfig | None = None,
        handlers: Mapping[str, ReplaySandboxHandler] | None = None,
    ) -> None:
        self._config = config or ReplaySandboxConfig()
        self._handlers: dict[str, ReplaySandboxHandler] = dict(handlers or {})

    @property
    def config(self) -> ReplaySandboxConfig:
        """Configuration du sandbox."""

        return self._config

    def register(self, event_type: str, handler: ReplaySandboxHandler) -> None:
        """Enregistre un handler de simulation pour un type d'événement."""

        if not event_type:
            raise ValueError("event_type must not be empty")
        self._handlers[event_type] = handler

    def replay(self, plan: ReplayPlan) -> ReplaySandboxResult:
        """Rejoue un plan dans le sandbox isolé.

        Les événements refusés produisent des étapes explicites. Les événements
        acceptés sans handler sont conservés comme étapes non manipulées : cela
        permet de vérifier l'ordre sans forcer un handler pour chaque type.
        """

        steps: list[ReplaySandboxStep] = []
        for index, event in enumerate(plan.events):
            if index >= self._config.max_events:
                steps.append(self._denied_step(index, event, "sandbox.max_events"))
                break

            reason = self._deny_reason(event)
            if reason:
                steps.append(self._denied_step(index, event, reason))
                continue

            handler = self._handlers.get(event.type)
            if handler is None:
                steps.append(self._accepted_step(index, event, handled=False))
                continue

            result = handler(event)
            steps.append(
                self._accepted_step(
                    index,
                    event,
                    handled=True,
                    result_repr=repr(result),
                )
            )

        return ReplaySandboxResult(
            source_record_count=plan.source_record_count,
            planned_event_count=plan.count,
            steps=tuple(steps),
        )

    def replay_types(self, plan: ReplayPlan) -> tuple[str, ...]:
        """Retourne les types que le sandbox traiterait, sans handler."""

        return self.replay(plan).event_types

    def _deny_reason(self, event: ReplayEvent) -> str:
        if self._config.allowed_types is not None:
            if event.type not in self._config.allowed_types:
                return "sandbox.type.not_allowed"

        if event.type in self._config.denied_types:
            return "sandbox.type.denied"

        return ""

    @staticmethod
    def _accepted_step(
        index: int,
        event: ReplayEvent,
        *,
        handled: bool,
        result_repr: str = "",
    ) -> ReplaySandboxStep:
        return ReplaySandboxStep(
            index=index,
            original_id=event.original_id,
            type=event.type,
            source=event.source,
            dest=event.dest,
            accepted=True,
            handled=handled,
            reason="accepted",
            result_repr=result_repr,
        )

    @staticmethod
    def _denied_step(index: int, event: ReplayEvent, reason: str) -> ReplaySandboxStep:
        return ReplaySandboxStep(
            index=index,
            original_id=event.original_id,
            type=event.type,
            source=event.source,
            dest=event.dest,
            accepted=False,
            handled=False,
            reason=reason,
        )


def replay_plan_types(plan: ReplayPlan, *, exclude: Iterable[str] = ()) -> tuple[str, ...]:
    """Retourne les types d'un ReplayPlan, avec exclusion explicite.

    Fonction pure utile pour les tests et pour les futures vues de replay.
    """

    excluded = set(exclude)
    return tuple(event.type for event in plan.events if event.type not in excluded)
