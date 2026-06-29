from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EventRecord:
    """Copie immuable et rejouable d'un événement observé.

    Un EventRecord ne transporte jamais le canal ``Request.reply``. Les Future
    asyncio restent une mécanique vivante du kernel et ne sont pas sérialisables.
    Le recorder capture donc uniquement les champs nécessaires à l'audit, au
    debug et au futur replay déterministe.
    """

    id: str
    type: str
    source: str
    dest: str
    priority: int
    timestamp_ns: int
    correlation_id: str | None = None
    payload_repr: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class EventLogSnapshot:
    """Image immuable du journal d'événements observé."""

    records: tuple[EventRecord, ...]

    @property
    def count(self) -> int:
        """Nombre d'événements capturés."""

        return len(self.records)

    @property
    def last_event_type(self) -> str | None:
        """Type du dernier événement capturé, s'il existe."""

        if not self.records:
            return None
        return self.records[-1].type


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    """Événement contrôlé dérivé d'un EventRecord.

    Phase 1.9 ne réinjecte pas encore ces événements dans le Scheduler. Cette
    structure prépare seulement une représentation sûre : pas de Future, pas de
    Request vivante, pas de désérialisation automatique du payload.
    """

    original_id: str
    type: str
    source: str
    dest: str
    priority: int
    timestamp_ns: int
    correlation_id: str | None = None
    payload_repr: str = ""
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True, slots=True)
class ReplayPlan:
    """Séquence immuable d'événements candidats au replay futur."""

    events: tuple[ReplayEvent, ...]
    source_record_count: int

    @property
    def count(self) -> int:
        """Nombre d'événements conservés dans le plan."""

        return len(self.events)

    @property
    def event_types(self) -> tuple[str, ...]:
        """Types d'événements présents dans l'ordre du plan."""

        return tuple(event.type for event in self.events)


@dataclass(frozen=True, slots=True)
class ReplaySandboxStep:
    """Résultat immuable d'une étape de replay isolé.

    Une étape ne contient aucun Event vivant. Elle décrit seulement ce que le
    sandbox a accepté, refusé ou confié à un handler de simulation.
    """

    index: int
    original_id: str
    type: str
    source: str
    dest: str
    accepted: bool
    handled: bool
    reason: str = ""
    result_repr: str = ""


@dataclass(frozen=True, slots=True)
class ReplaySandboxResult:
    """Bilan immuable d'une exécution ReplaySandbox."""

    source_record_count: int
    planned_event_count: int
    steps: tuple[ReplaySandboxStep, ...]

    @property
    def accepted_count(self) -> int:
        """Nombre d'étapes acceptées par le sandbox."""

        return sum(1 for step in self.steps if step.accepted)

    @property
    def rejected_count(self) -> int:
        """Nombre d'étapes refusées par le sandbox."""

        return sum(1 for step in self.steps if not step.accepted)

    @property
    def handled_count(self) -> int:
        """Nombre d'étapes acceptées ayant un handler de simulation."""

        return sum(1 for step in self.steps if step.handled)

    @property
    def ok(self) -> bool:
        """Indique si toutes les étapes planifiées ont été acceptées."""

        return self.rejected_count == 0 and len(self.steps) == self.planned_event_count

    @property
    def event_types(self) -> tuple[str, ...]:
        """Types d'événements traités dans l'ordre."""

        return tuple(step.type for step in self.steps)
