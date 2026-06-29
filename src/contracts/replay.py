from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _default_denied_replay_types() -> frozenset[str]:
    return frozenset({"SHUTDOWN"})


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
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


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
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)


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


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    """Scénario immuable de replay isolé.

    Un scénario décrit uniquement comment un ReplayPlan doit être simulé. Il ne
    connaît pas le Scheduler et ne contient pas de handler vivant. Les handlers
    restent fournis au runner, afin de garder ce contrat sérialisable et stable.
    """

    name: str
    plan: ReplayPlan
    max_events: int = 1_000
    allowed_types: frozenset[str] | None = None
    denied_types: frozenset[str] = field(default_factory=_default_denied_replay_types)
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ReplayScenario.name must not be empty")
        if self.max_events <= 0:
            raise ValueError("ReplayScenario.max_events must be positive")


@dataclass(frozen=True, slots=True)
class ReplayScenarioResult:
    """Résultat immuable d'un scénario de replay."""

    scenario_name: str
    tags: tuple[str, ...]
    sandbox_result: ReplaySandboxResult

    @property
    def ok(self) -> bool:
        """Indique si le scénario a réussi sans refus sandbox."""

        return self.sandbox_result.ok

    @property
    def accepted_count(self) -> int:
        """Nombre d'événements acceptés pour ce scénario."""

        return self.sandbox_result.accepted_count

    @property
    def rejected_count(self) -> int:
        """Nombre d'événements refusés pour ce scénario."""

        return self.sandbox_result.rejected_count

    @property
    def handled_count(self) -> int:
        """Nombre d'événements manipulés par des handlers de simulation."""

        return self.sandbox_result.handled_count


@dataclass(frozen=True, slots=True)
class ReplayReport:
    """Rapport déterministe de plusieurs scénarios de replay."""

    scenario_results: tuple[ReplayScenarioResult, ...]

    @property
    def scenario_count(self) -> int:
        """Nombre de scénarios inclus dans le rapport."""

        return len(self.scenario_results)

    @property
    def ok(self) -> bool:
        """Indique si tous les scénarios ont réussi."""

        return all(result.ok for result in self.scenario_results)

    @property
    def accepted_count(self) -> int:
        """Total des événements acceptés par tous les scénarios."""

        return sum(result.accepted_count for result in self.scenario_results)

    @property
    def rejected_count(self) -> int:
        """Total des événements refusés par tous les scénarios."""

        return sum(result.rejected_count for result in self.scenario_results)

    @property
    def handled_count(self) -> int:
        """Total des événements manipulés par handlers de simulation."""

        return sum(result.handled_count for result in self.scenario_results)

    @property
    def scenario_names(self) -> tuple[str, ...]:
        """Noms de scénarios dans l'ordre du rapport."""

        return tuple(result.scenario_name for result in self.scenario_results)

    def to_lines(self) -> tuple[str, ...]:
        """Produit une représentation textuelle stable du rapport.

        Cette sortie est déterministe : pas d'horodatage, pas d'ordre dépendant
        d'un dictionnaire, pas de contenu runtime non sérialisable.
        """

        status = "OK" if self.ok else "FAILED"
        lines = [
            f"ReplayReport: {status}",
            f"scenarios={self.scenario_count}",
            f"accepted={self.accepted_count}",
            f"rejected={self.rejected_count}",
            f"handled={self.handled_count}",
        ]
        for result in self.scenario_results:
            scenario_status = "OK" if result.ok else "FAILED"
            lines.append(
                "scenario="
                f"{result.scenario_name} "
                f"status={scenario_status} "
                f"accepted={result.accepted_count} "
                f"rejected={result.rejected_count} "
                f"handled={result.handled_count}"
            )
        return tuple(lines)
