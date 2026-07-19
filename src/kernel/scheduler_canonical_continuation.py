from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from typing import Any, Protocol

from kernel.scheduler_task_graph import (
    SchedulerTaskGraph,
    SchedulerTaskGraphPromotion,
)
from kernel.scheduler_task_model import SchedulerTaskState

_SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class SchedulerCanonicalContinuationError(ValueError):
    """Erreur de contrat de la continuation durable du Scheduler."""


class SchedulerContinuationStatus(str, Enum):
    """État calculé après relecture de l'autorité durable."""

    READY = "ready"
    RUNNING = "running"
    RETRY_WAIT = "retry-wait"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"


@dataclass(frozen=True, slots=True)
class SchedulerCanonicalCycleBound:
    """Borne explicite d'un tick du Scheduler canonique."""

    max_task_steps: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_task_steps, bool)
            or not isinstance(self.max_task_steps, int)
            or not 1 <= self.max_task_steps <= 64
        ):
            raise SchedulerCanonicalContinuationError(
                "max_task_steps doit être compris entre 1 et 64"
            )


@dataclass(frozen=True, slots=True)
class SchedulerDurableGraphSnapshot:
    """Graphe typé relu depuis PostgreSQL après un commit durable."""

    command_ref: str
    scheduler_ref: str
    durable_revision: int
    loaded_at: str
    graph: SchedulerTaskGraph
    source_transaction_ref: str
    snapshot_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _require_positive_int("durable_revision", self.durable_revision)
        _require_utc("loaded_at", self.loaded_at)
        if self.source_transaction_ref:
            _require_typed_ref("source_transaction_ref", self.source_transaction_ref)
        if self.graph.command_ref != self.command_ref:
            raise SchedulerCanonicalContinuationError(
                "le graphe relu ne correspond pas à command_ref"
            )
        _require_sha256("snapshot_digest", self.snapshot_digest)
        expected = _snapshot_digest(
            command_ref=self.command_ref,
            scheduler_ref=self.scheduler_ref,
            durable_revision=self.durable_revision,
            loaded_at=self.loaded_at,
            graph_digest=self.graph.graph_digest,
            source_transaction_ref=self.source_transaction_ref,
        )
        if expected != self.snapshot_digest:
            raise SchedulerCanonicalContinuationError(
                "snapshot_digest incohérent"
            )

    @classmethod
    def create(
        cls,
        *,
        command_ref: str,
        scheduler_ref: str,
        durable_revision: int,
        loaded_at: str,
        graph: SchedulerTaskGraph,
        source_transaction_ref: str = "",
    ) -> SchedulerDurableGraphSnapshot:
        values = dict(
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            durable_revision=durable_revision,
            loaded_at=loaded_at,
            graph=graph,
            source_transaction_ref=source_transaction_ref,
        )
        return cls(
            snapshot_digest=_snapshot_digest(
                command_ref=command_ref,
                scheduler_ref=scheduler_ref,
                durable_revision=durable_revision,
                loaded_at=loaded_at,
                graph_digest=graph.graph_digest,
                source_transaction_ref=source_transaction_ref,
            ),
            **values,
        )


@dataclass(frozen=True, slots=True)
class SchedulerContinuationDecision:
    """Décision pure issue du graphe relu et de sa promotion éventuelle."""

    decision_ref: str
    status: SchedulerContinuationStatus
    snapshot_before: SchedulerDurableGraphSnapshot
    promotion: SchedulerTaskGraphPromotion
    ready_task_refs: tuple[str, ...]
    running_task_refs: tuple[str, ...]
    retry_wait_task_refs: tuple[str, ...]
    blocked_task_refs: tuple[str, ...]
    terminal_task_refs: tuple[str, ...]
    decided_at: str
    actor_ref: str
    cause_ref: str
    decision_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("decision_ref", self.decision_ref, "scheduler-decision:")
        _require_utc("decided_at", self.decided_at)
        _require_typed_ref("actor_ref", self.actor_ref)
        _require_typed_ref("cause_ref", self.cause_ref)
        for name, refs in (
            ("ready_task_refs", self.ready_task_refs),
            ("running_task_refs", self.running_task_refs),
            ("retry_wait_task_refs", self.retry_wait_task_refs),
            ("blocked_task_refs", self.blocked_task_refs),
            ("terminal_task_refs", self.terminal_task_refs),
        ):
            _require_unique_task_refs(name, refs)
        expected_groups = _group_task_refs(self.promotion.graph)
        actual_groups = (
            self.ready_task_refs,
            self.running_task_refs,
            self.retry_wait_task_refs,
            self.blocked_task_refs,
            self.terminal_task_refs,
        )
        if actual_groups != expected_groups:
            raise SchedulerCanonicalContinuationError(
                "les groupes de tâches divergent du graphe promu"
            )
        expected_status = _continuation_status(self.promotion.graph)
        if self.status is not expected_status:
            raise SchedulerCanonicalContinuationError(
                "le statut de continuation diverge du graphe promu"
            )
        _require_sha256("decision_digest", self.decision_digest)
        expected = _decision_digest(
            snapshot_digest=self.snapshot_before.snapshot_digest,
            promoted_graph_digest=self.promotion.graph.graph_digest,
            status=self.status,
            ready_task_refs=self.ready_task_refs,
            running_task_refs=self.running_task_refs,
            retry_wait_task_refs=self.retry_wait_task_refs,
            blocked_task_refs=self.blocked_task_refs,
            terminal_task_refs=self.terminal_task_refs,
            decided_at=self.decided_at,
            actor_ref=self.actor_ref,
            cause_ref=self.cause_ref,
        )
        if expected != self.decision_digest:
            raise SchedulerCanonicalContinuationError(
                "decision_digest incohérent"
            )
        if self.decision_ref != (
            "scheduler-decision:" + _bare_digest(expected)[:24]
        ):
            raise SchedulerCanonicalContinuationError(
                "decision_ref incohérent"
            )

    @property
    def next_ready_task_ref(self) -> str:
        return self.ready_task_refs[0] if self.ready_task_refs else ""


class SchedulerDurableContinuationStore(Protocol):
    """Port PostgreSQL de relecture et de commit de promotion."""

    def load_snapshot(
        self,
        *,
        command_ref: str,
        scheduler_ref: str,
        loaded_at: str,
    ) -> SchedulerDurableGraphSnapshot: ...

    def commit_promotion(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        promotion: SchedulerTaskGraphPromotion,
        committed_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerDurableGraphSnapshot: ...


class SchedulerReadyTaskStepRunner(Protocol):
    """Pipeline injecté admission→lancement→exécution→commit de fin."""

    async def run_ready_task(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        task_ref: str,
    ) -> Any: ...


class SchedulerDurableContinuationPlanner:
    """Relit conceptuellement le graphe et calcule sa suite sans effet métier."""

    def plan(
        self,
        *,
        snapshot: SchedulerDurableGraphSnapshot,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerContinuationDecision:
        promotion = snapshot.graph.promote_ready(
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        groups = _group_task_refs(promotion.graph)
        status = _continuation_status(promotion.graph)
        digest = _decision_digest(
            snapshot_digest=snapshot.snapshot_digest,
            promoted_graph_digest=promotion.graph.graph_digest,
            status=status,
            ready_task_refs=groups[0],
            running_task_refs=groups[1],
            retry_wait_task_refs=groups[2],
            blocked_task_refs=groups[3],
            terminal_task_refs=groups[4],
            decided_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        return SchedulerContinuationDecision(
            decision_ref="scheduler-decision:" + _bare_digest(digest)[:24],
            status=status,
            snapshot_before=snapshot,
            promotion=promotion,
            ready_task_refs=groups[0],
            running_task_refs=groups[1],
            retry_wait_task_refs=groups[2],
            blocked_task_refs=groups[3],
            terminal_task_refs=groups[4],
            decided_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
            decision_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class SchedulerCanonicalCycleReport:
    """Rapport immuable d'un tick borné du Scheduler canonique."""

    cycle_ref: str
    command_ref: str
    scheduler_ref: str
    started_at: str
    finished_at: str
    max_task_steps: int
    completed_task_steps: int
    stopped_cooperatively: bool
    bound_exhausted: bool
    final_status: SchedulerContinuationStatus
    decision_refs: tuple[str, ...]
    outcome_refs: tuple[str, ...]
    final_snapshot_digest: str
    cycle_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("cycle_ref", self.cycle_ref, "scheduler-cycle:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _require_utc("started_at", self.started_at)
        _require_utc("finished_at", self.finished_at)
        _require_positive_int("max_task_steps", self.max_task_steps)
        if (
            isinstance(self.completed_task_steps, bool)
            or not isinstance(self.completed_task_steps, int)
            or not 0 <= self.completed_task_steps <= self.max_task_steps
        ):
            raise SchedulerCanonicalContinuationError(
                "completed_task_steps hors borne"
            )
        if not isinstance(self.stopped_cooperatively, bool):
            raise SchedulerCanonicalContinuationError(
                "stopped_cooperatively doit être booléen"
            )
        if not isinstance(self.bound_exhausted, bool):
            raise SchedulerCanonicalContinuationError(
                "bound_exhausted doit être booléen"
            )
        if len(self.outcome_refs) != self.completed_task_steps:
            raise SchedulerCanonicalContinuationError(
                "outcome_refs diverge du nombre d'étapes"
            )
        _require_unique_refs("decision_refs", self.decision_refs)
        _require_unique_refs("outcome_refs", self.outcome_refs)
        _require_sha256("final_snapshot_digest", self.final_snapshot_digest)
        _require_sha256("cycle_digest", self.cycle_digest)
        expected = _cycle_digest(
            command_ref=self.command_ref,
            scheduler_ref=self.scheduler_ref,
            started_at=self.started_at,
            finished_at=self.finished_at,
            max_task_steps=self.max_task_steps,
            completed_task_steps=self.completed_task_steps,
            stopped_cooperatively=self.stopped_cooperatively,
            bound_exhausted=self.bound_exhausted,
            final_status=self.final_status,
            decision_refs=self.decision_refs,
            outcome_refs=self.outcome_refs,
            final_snapshot_digest=self.final_snapshot_digest,
        )
        if expected != self.cycle_digest:
            raise SchedulerCanonicalContinuationError("cycle_digest incohérent")
        if self.cycle_ref != "scheduler-cycle:" + _bare_digest(expected)[:24]:
            raise SchedulerCanonicalContinuationError("cycle_ref incohérent")


class SchedulerCanonicalBoundedCycle:
    """Exécute un nombre borné d'étapes dans le Scheduler déjà actif."""

    def __init__(
        self,
        *,
        store: SchedulerDurableContinuationStore,
        step_runner: SchedulerReadyTaskStepRunner,
        clock: Callable[[], str],
        running_probe: Callable[[], bool],
        planner: SchedulerDurableContinuationPlanner | None = None,
    ) -> None:
        self._store = store
        self._step_runner = step_runner
        self._clock = clock
        self._running_probe = running_probe
        self._planner = planner or SchedulerDurableContinuationPlanner()

    async def run(
        self,
        *,
        command_ref: str,
        scheduler_ref: str,
        actor_ref: str,
        cause_ref: str,
        bound: SchedulerCanonicalCycleBound,
    ) -> SchedulerCanonicalCycleReport:
        _require_typed_ref("command_ref", command_ref, "scheduler-command:")
        _require_typed_ref("scheduler_ref", scheduler_ref, "scheduler:")
        _require_typed_ref("actor_ref", actor_ref)
        _require_typed_ref("cause_ref", cause_ref)
        if not self._running_probe():
            raise SchedulerCanonicalContinuationError(
                "le Scheduler canonique doit déjà être actif"
            )

        started_at = self._clock()
        snapshot = self._store.load_snapshot(
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            loaded_at=started_at,
        )
        decisions: list[str] = []
        outcomes: list[str] = []
        final_status = _continuation_status(snapshot.graph)
        stopped = False

        for _step_index in range(bound.max_task_steps):
            if not self._running_probe():
                stopped = True
                break
            decided_at = self._clock()
            decision = self._planner.plan(
                snapshot=snapshot,
                occurred_at=decided_at,
                actor_ref=actor_ref,
                cause_ref=cause_ref,
            )
            decisions.append(decision.decision_ref)
            if decision.promotion.changed:
                snapshot = self._store.commit_promotion(
                    snapshot=snapshot,
                    promotion=decision.promotion,
                    committed_at=decided_at,
                    actor_ref=actor_ref,
                    cause_ref=cause_ref,
                )
            final_status = decision.status
            if decision.status is not SchedulerContinuationStatus.READY:
                break

            task_ref = decision.next_ready_task_ref
            outcome = await self._step_runner.run_ready_task(
                snapshot=snapshot,
                task_ref=task_ref,
            )
            outcome_ref = str(getattr(outcome, "outcome_ref", ""))
            _require_typed_ref(
                "outcome.outcome_ref",
                outcome_ref,
                "handler-outcome:",
            )
            outcomes.append(outcome_ref)
            reloaded_at = self._clock()
            snapshot = self._store.load_snapshot(
                command_ref=command_ref,
                scheduler_ref=scheduler_ref,
                loaded_at=reloaded_at,
            )
            if snapshot.graph.task(task_ref).state is SchedulerTaskState.READY:
                raise SchedulerCanonicalContinuationError(
                    "le pipeline d'étape n'a pas avancé durablement la tâche"
                )
            final_status = _continuation_status(snapshot.graph)

        bound_exhausted = (
            not stopped
            and len(outcomes) == bound.max_task_steps
            and final_status
            in {
                SchedulerContinuationStatus.READY,
                SchedulerContinuationStatus.RUNNING,
                SchedulerContinuationStatus.RETRY_WAIT,
                SchedulerContinuationStatus.BLOCKED,
            }
        )
        finished_at = self._clock()
        digest = _cycle_digest(
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            started_at=started_at,
            finished_at=finished_at,
            max_task_steps=bound.max_task_steps,
            completed_task_steps=len(outcomes),
            stopped_cooperatively=stopped,
            bound_exhausted=bound_exhausted,
            final_status=final_status,
            decision_refs=tuple(decisions),
            outcome_refs=tuple(outcomes),
            final_snapshot_digest=snapshot.snapshot_digest,
        )
        return SchedulerCanonicalCycleReport(
            cycle_ref="scheduler-cycle:" + _bare_digest(digest)[:24],
            command_ref=command_ref,
            scheduler_ref=scheduler_ref,
            started_at=started_at,
            finished_at=finished_at,
            max_task_steps=bound.max_task_steps,
            completed_task_steps=len(outcomes),
            stopped_cooperatively=stopped,
            bound_exhausted=bound_exhausted,
            final_status=final_status,
            decision_refs=tuple(decisions),
            outcome_refs=tuple(outcomes),
            final_snapshot_digest=snapshot.snapshot_digest,
            cycle_digest=digest,
        )


def _group_task_refs(
    graph: SchedulerTaskGraph,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    ready = tuple(
        task.task_ref
        for task in sorted(
            (item for item in graph.tasks if item.state is SchedulerTaskState.READY),
            key=lambda item: (-item.effective_priority, item.created_at, item.task_ref),
        )
    )
    running = tuple(
        task.task_ref
        for task in graph.tasks
        if task.state is SchedulerTaskState.RUNNING
    )
    retry_wait = tuple(
        task.task_ref
        for task in graph.tasks
        if task.state is SchedulerTaskState.RETRY_WAIT
    )
    blocked = tuple(
        task.task_ref
        for task in graph.tasks
        if task.state
        in {
            SchedulerTaskState.PLANNED,
            SchedulerTaskState.PAUSED,
        }
    )
    terminal = tuple(task.task_ref for task in graph.tasks if task.state.terminal)
    return ready, running, retry_wait, blocked, terminal


def _continuation_status(graph: SchedulerTaskGraph) -> SchedulerContinuationStatus:
    states = tuple(task.state for task in graph.tasks)
    if any(state is SchedulerTaskState.READY for state in states):
        return SchedulerContinuationStatus.READY
    if any(state is SchedulerTaskState.RUNNING for state in states):
        return SchedulerContinuationStatus.RUNNING
    if any(state is SchedulerTaskState.RETRY_WAIT for state in states):
        return SchedulerContinuationStatus.RETRY_WAIT
    if any(
        state in {SchedulerTaskState.PLANNED, SchedulerTaskState.PAUSED}
        for state in states
    ):
        return SchedulerContinuationStatus.BLOCKED
    if any(state is SchedulerTaskState.FAILED for state in states):
        return SchedulerContinuationStatus.FAILED
    if any(state is SchedulerTaskState.TIMED_OUT for state in states):
        return SchedulerContinuationStatus.TIMED_OUT
    if any(state is SchedulerTaskState.CANCELLED for state in states):
        return SchedulerContinuationStatus.CANCELLED
    return SchedulerContinuationStatus.COMPLETED


def _snapshot_digest(
    *,
    command_ref: str,
    scheduler_ref: str,
    durable_revision: int,
    loaded_at: str,
    graph_digest: str,
    source_transaction_ref: str,
) -> str:
    return "sha256:" + _length_prefixed_digest(
        (
            ("command_ref", command_ref),
            ("scheduler_ref", scheduler_ref),
            ("durable_revision", durable_revision),
            ("loaded_at", loaded_at),
            ("graph_digest", graph_digest),
            ("source_transaction_ref", source_transaction_ref),
        )
    )


def _decision_digest(
    *,
    snapshot_digest: str,
    promoted_graph_digest: str,
    status: SchedulerContinuationStatus,
    ready_task_refs: tuple[str, ...],
    running_task_refs: tuple[str, ...],
    retry_wait_task_refs: tuple[str, ...],
    blocked_task_refs: tuple[str, ...],
    terminal_task_refs: tuple[str, ...],
    decided_at: str,
    actor_ref: str,
    cause_ref: str,
) -> str:
    parts: list[tuple[str, object]] = [
        ("snapshot_digest", snapshot_digest),
        ("promoted_graph_digest", promoted_graph_digest),
        ("status", status),
        ("decided_at", decided_at),
        ("actor_ref", actor_ref),
        ("cause_ref", cause_ref),
    ]
    for name, refs in (
        ("ready", ready_task_refs),
        ("running", running_task_refs),
        ("retry_wait", retry_wait_task_refs),
        ("blocked", blocked_task_refs),
        ("terminal", terminal_task_refs),
    ):
        parts.extend((name, value) for value in refs)
    return "sha256:" + _length_prefixed_digest(tuple(parts))


def _cycle_digest(
    *,
    command_ref: str,
    scheduler_ref: str,
    started_at: str,
    finished_at: str,
    max_task_steps: int,
    completed_task_steps: int,
    stopped_cooperatively: bool,
    bound_exhausted: bool,
    final_status: SchedulerContinuationStatus,
    decision_refs: tuple[str, ...],
    outcome_refs: tuple[str, ...],
    final_snapshot_digest: str,
) -> str:
    parts: list[tuple[str, object]] = [
        ("command_ref", command_ref),
        ("scheduler_ref", scheduler_ref),
        ("started_at", started_at),
        ("finished_at", finished_at),
        ("max_task_steps", max_task_steps),
        ("completed_task_steps", completed_task_steps),
        ("stopped_cooperatively", stopped_cooperatively),
        ("bound_exhausted", bound_exhausted),
        ("final_status", final_status),
        ("final_snapshot_digest", final_snapshot_digest),
    ]
    parts.extend(("decision_ref", value) for value in decision_refs)
    parts.extend(("outcome_ref", value) for value in outcome_refs)
    return "sha256:" + _length_prefixed_digest(tuple(parts))


def _length_prefixed_digest(parts: tuple[tuple[str, object], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in parts:
        key = name.encode("utf-8")
        encoded = _scalar_text(value).encode("utf-8")
        digest.update(len(key).to_bytes(4, "big"))
        digest.update(key)
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _scalar_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (str, int)):
        return str(value)
    raise SchedulerCanonicalContinuationError(
        f"type scalaire non pris en charge: {type(value).__name__}"
    )


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise SchedulerCanonicalContinuationError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise SchedulerCanonicalContinuationError(
            f"{name} doit commencer par {prefix}"
        )


def _require_utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise SchedulerCanonicalContinuationError(
            f"{name} doit être un horodatage UTC finissant par Z"
        )


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SchedulerCanonicalContinuationError(
            f"{name} doit être un entier strictement positif"
        )


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SchedulerCanonicalContinuationError(
            f"{name} doit être un SHA-256 minuscule"
        )


def _require_unique_task_refs(name: str, refs: tuple[str, ...]) -> None:
    _require_unique_refs(name, refs)
    for value in refs:
        _require_typed_ref(name, value, "scheduler-task:")


def _require_unique_refs(name: str, refs: tuple[str, ...]) -> None:
    if len(set(refs)) != len(refs):
        raise SchedulerCanonicalContinuationError(f"{name} contient un doublon")
    for value in refs:
        _require_typed_ref(name, value)


__all__ = (
    "SchedulerCanonicalBoundedCycle",
    "SchedulerCanonicalContinuationError",
    "SchedulerCanonicalCycleBound",
    "SchedulerCanonicalCycleReport",
    "SchedulerContinuationDecision",
    "SchedulerContinuationStatus",
    "SchedulerDurableContinuationPlanner",
    "SchedulerDurableContinuationStore",
    "SchedulerDurableGraphSnapshot",
    "SchedulerReadyTaskStepRunner",
)
