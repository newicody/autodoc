"""Composition bornée du cycle de recherche dans le Scheduler externe.

Le service OpenRC possède le processus et le Scheduler canonique. Cette unité
ne démarre aucun thread, daemon, event loop ou second Scheduler. Elle réclame au
plus une commande SQL par tick, exécute un cycle borné déjà injecté et persiste
ensuite les notices de cycle de vie dans une table relationnelle dédiée.

Les notices sont tamponnées pendant l'exécution. Leur persistance intervient
après le commit métier du cycle et reste observation-only : une panne du store
d'observation est rapportée mais ne réécrit jamais l'issue durable des tâches.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import hashlib
from typing import Any, Protocol

from context.github_research_scheduler_command_claim_0287 import (
    RunningSchedulerView,
    SchedulerCommandClaimStore,
    claim_next_for_running_canonical_scheduler,
)
from kernel.scheduler_canonical_continuation import (
    SchedulerCanonicalBoundedCycle,
    SchedulerCanonicalCycleBound,
    SchedulerCanonicalCycleReport,
)
from kernel.scheduler_handler_contract import (
    HandlerInformationSink,
    HandlerLifecycleNotice,
)

EXTERNALLY_MANAGED_RUNTIME_SCHEMA = (
    "missipy.github.research_love_externally_managed_runtime.v1"
)
TEMPORAL_OBSERVATION_SCHEMA = (
    "missipy.scheduler.handler_temporal_observation.v1"
)
RUNTIME_TICK_SCHEMA = "missipy.scheduler.externally_managed_tick.v1"


class GitHubResearchLoveExternallyManagedRuntimeError(RuntimeError):
    """Erreur de composition ou de persistance passive du runtime installé."""


class FullGroupedSchedulerBootstrapView(Protocol):
    """Vue minimale du bootstrap complet des dix handlers."""

    handler_refs: tuple[str, ...]
    capability_refs: tuple[str, ...]
    catalog: Any
    factory: Any


@dataclass(frozen=True, slots=True)
class SchedulerTemporalObservation:
    schema: str
    observation_ref: str
    scheduler_ref: str
    handler_ref: str
    capability_ref: str
    phase: str
    level: str
    text: str
    occurred_at: str
    command_ref: str = ""
    task_ref: str = ""
    result_ref: str = ""
    attempt: int = 0

    def __post_init__(self) -> None:
        if self.schema != TEMPORAL_OBSERVATION_SCHEMA:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "schéma d'observation temporelle non pris en charge"
            )
        for name, value, prefix in (
            ("observation_ref", self.observation_ref, "scheduler-observation:"),
            ("scheduler_ref", self.scheduler_ref, "scheduler:"),
            ("handler_ref", self.handler_ref, "handler:"),
            ("capability_ref", self.capability_ref, "capability:"),
        ):
            if not value.startswith(prefix):
                raise GitHubResearchLoveExternallyManagedRuntimeError(
                    f"{name} doit commencer par {prefix}"
                )
        if "T" not in self.occurred_at or not self.occurred_at.endswith("Z"):
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "occurred_at doit être UTC et terminé par Z"
            )
        if self.attempt < 0:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "attempt ne peut pas être négatif"
            )


class SchedulerTemporalObservationStore(Protocol):
    def initialize_schema(self) -> None: ...

    def append_many(
        self,
        observations: Sequence[SchedulerTemporalObservation],
    ) -> int: ...


class DbApiSchedulerTemporalObservationStore:
    """Projection relationnelle passive, sans JSON et sans choix Scheduler."""

    def __init__(self, connection: Any, *, paramstyle: str = "format") -> None:
        if paramstyle not in {"format", "qmark"}:
            raise ValueError("paramstyle doit être format ou qmark")
        self._connection = connection
        self._placeholder = "%s" if paramstyle == "format" else "?"

    def initialize_schema(self) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduler_handler_temporal_observations (
                    observation_ref TEXT PRIMARY KEY,
                    scheduler_ref TEXT NOT NULL,
                    command_ref TEXT NOT NULL,
                    task_ref TEXT NOT NULL,
                    handler_ref TEXT NOT NULL,
                    capability_ref TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    level TEXT NOT NULL,
                    text_value TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    result_ref TEXT NOT NULL,
                    attempt INTEGER NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS
                scheduler_handler_temporal_observations_time_idx
                ON scheduler_handler_temporal_observations
                (occurred_at, handler_ref, phase)
                """
            )
        finally:
            cursor.close()
        self._connection.commit()

    def append_many(
        self,
        observations: Sequence[SchedulerTemporalObservation],
    ) -> int:
        if not observations:
            return 0
        cursor = self._connection.cursor()
        inserted = 0
        marks = ", ".join([self._placeholder] * 12)
        sql = (
            "INSERT INTO scheduler_handler_temporal_observations ("
            "observation_ref, scheduler_ref, command_ref, task_ref, handler_ref, "
            "capability_ref, phase, level, text_value, occurred_at, result_ref, attempt"
            f") VALUES ({marks}) ON CONFLICT(observation_ref) DO NOTHING"
        )
        try:
            for value in observations:
                before = getattr(cursor, "rowcount", -1)
                cursor.execute(
                    sql,
                    (
                        value.observation_ref,
                        value.scheduler_ref,
                        value.command_ref,
                        value.task_ref,
                        value.handler_ref,
                        value.capability_ref,
                        value.phase,
                        value.level,
                        value.text,
                        value.occurred_at,
                        value.result_ref,
                        value.attempt,
                    ),
                )
                after = getattr(cursor, "rowcount", -1)
                if after == 1 or (before == -1 and after == -1):
                    inserted += 1
        except Exception:
            self._connection.rollback()
            raise
        finally:
            cursor.close()
        self._connection.commit()
        return inserted


@dataclass(slots=True)
class BufferedPersistentHandlerInformationSink(HandlerInformationSink):
    """Tamponne les notices puis les projette après le commit métier."""

    scheduler_ref: str
    clock: Callable[[], str]
    downstream: HandlerInformationSink | None = None
    _pending: list[SchedulerTemporalObservation] = field(
        default_factory=list,
        init=False,
        repr=False,
    )

    def publish(self, notice: HandlerLifecycleNotice) -> None:
        occurred_at = self.clock()
        attributes = notice.attributes
        command_ref = str(attributes.get("command_ref", ""))
        task_ref = str(attributes.get("task_ref", ""))
        result_ref = str(attributes.get("result_ref", ""))
        attempt_value = attributes.get("attempt", 0)
        attempt = int(attempt_value) if str(attempt_value).isdigit() else 0
        digest = _observation_digest(
            scheduler_ref=self.scheduler_ref,
            notice=notice,
            occurred_at=occurred_at,
            command_ref=command_ref,
            task_ref=task_ref,
            result_ref=result_ref,
            attempt=attempt,
        )
        self._pending.append(
            SchedulerTemporalObservation(
                schema=TEMPORAL_OBSERVATION_SCHEMA,
                observation_ref="scheduler-observation:" + digest[:24],
                scheduler_ref=self.scheduler_ref,
                handler_ref=notice.handler_ref,
                capability_ref=notice.capability_ref,
                phase=notice.phase.value,
                level=notice.level.value,
                text=notice.text,
                occurred_at=occurred_at,
                command_ref=command_ref,
                task_ref=task_ref,
                result_ref=result_ref,
                attempt=attempt,
            )
        )
        if self.downstream is not None:
            try:
                self.downstream.publish(notice)
            except Exception:
                pass

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def flush(self, store: SchedulerTemporalObservationStore) -> tuple[int, str]:
        values = tuple(self._pending)
        if not values:
            return 0, ""
        try:
            inserted = store.append_many(values)
        except Exception as exc:  # observation-only : le métier reste commité
            return 0, type(exc).__name__
        self._pending.clear()
        return inserted, ""


@dataclass(frozen=True, slots=True)
class ExternallyManagedSchedulerTickReport:
    schema: str
    runtime_schema: str
    scheduler_ref: str
    status: str
    claimed_command_ref: str
    cycle_report: SchedulerCanonicalCycleReport | None
    observations_inserted: int
    observation_error_type: str

    def __post_init__(self) -> None:
        if self.schema != RUNTIME_TICK_SCHEMA:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "schéma de tick non pris en charge"
            )
        if self.runtime_schema != EXTERNALLY_MANAGED_RUNTIME_SCHEMA:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "runtime_schema incohérent"
            )
        if self.status not in {"idle", "cycle-executed"}:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "statut de tick non pris en charge"
            )
        if (self.cycle_report is None) != (self.status == "idle"):
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "cycle_report diverge du statut"
            )


@dataclass(slots=True)
class GitHubResearchLoveExternallyManagedRuntime:
    """Un tick explicite dans le Scheduler que le service possède déjà."""

    scheduler: RunningSchedulerView
    scheduler_ref: str
    command_store: SchedulerCommandClaimStore
    bootstrap: FullGroupedSchedulerBootstrapView
    cycle: SchedulerCanonicalBoundedCycle
    observation_sink: BufferedPersistentHandlerInformationSink
    observation_store: SchedulerTemporalObservationStore
    clock: Callable[[], str]

    def __post_init__(self) -> None:
        if not self.scheduler_ref.startswith("scheduler:"):
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "scheduler_ref doit être typé"
            )
        if len(self.bootstrap.handler_refs) != 10:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "le runtime exige le bootstrap complet des dix handlers"
            )
        if len(self.bootstrap.capability_refs) != 10:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "le runtime exige dix capacités"
            )
        if self.observation_sink.scheduler_ref != self.scheduler_ref:
            raise GitHubResearchLoveExternallyManagedRuntimeError(
                "le sink d'observation appartient à un autre Scheduler"
            )

    async def run_tick(
        self,
        *,
        actor_ref: str,
        cause_ref: str,
        bound: SchedulerCanonicalCycleBound,
    ) -> ExternallyManagedSchedulerTickReport:
        claimed_at = self.clock()
        claim_result = claim_next_for_running_canonical_scheduler(
            scheduler=self.scheduler,
            command_store=self.command_store,
            scheduler_ref=self.scheduler_ref,
            claimed_at=claimed_at,
        )
        if claim_result.claim is None:
            inserted, error_type = self.observation_sink.flush(
                self.observation_store
            )
            return ExternallyManagedSchedulerTickReport(
                schema=RUNTIME_TICK_SCHEMA,
                runtime_schema=EXTERNALLY_MANAGED_RUNTIME_SCHEMA,
                scheduler_ref=self.scheduler_ref,
                status="idle",
                claimed_command_ref="",
                cycle_report=None,
                observations_inserted=inserted,
                observation_error_type=error_type,
            )
        command_ref = claim_result.claim.command.command_ref
        cycle_report = await self.cycle.run(
            command_ref=command_ref,
            scheduler_ref=self.scheduler_ref,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
            bound=bound,
        )
        inserted, error_type = self.observation_sink.flush(
            self.observation_store
        )
        return ExternallyManagedSchedulerTickReport(
            schema=RUNTIME_TICK_SCHEMA,
            runtime_schema=EXTERNALLY_MANAGED_RUNTIME_SCHEMA,
            scheduler_ref=self.scheduler_ref,
            status="cycle-executed",
            claimed_command_ref=command_ref,
            cycle_report=cycle_report,
            observations_inserted=inserted,
            observation_error_type=error_type,
        )


def _observation_digest(
    *,
    scheduler_ref: str,
    notice: HandlerLifecycleNotice,
    occurred_at: str,
    command_ref: str,
    task_ref: str,
    result_ref: str,
    attempt: int,
) -> str:
    values = (
        scheduler_ref,
        notice.handler_ref,
        notice.capability_ref,
        notice.phase.value,
        notice.level.value,
        notice.text,
        occurred_at,
        command_ref,
        task_ref,
        result_ref,
        str(attempt),
    )
    payload = "".join(f"{len(value)}:{value}" for value in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = (
    "EXTERNALLY_MANAGED_RUNTIME_SCHEMA",
    "RUNTIME_TICK_SCHEMA",
    "TEMPORAL_OBSERVATION_SCHEMA",
    "BufferedPersistentHandlerInformationSink",
    "DbApiSchedulerTemporalObservationStore",
    "ExternallyManagedSchedulerTickReport",
    "FullGroupedSchedulerBootstrapView",
    "GitHubResearchLoveExternallyManagedRuntime",
    "GitHubResearchLoveExternallyManagedRuntimeError",
    "SchedulerTemporalObservation",
    "SchedulerTemporalObservationStore",
)
