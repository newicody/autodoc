from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import math
import re


_SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class SchedulerTaskModelError(ValueError):
    """Erreur de contrat du modèle interne des tâches Scheduler."""


class SchedulerTaskState(str, Enum):
    """États durables d'une tâche gouvernée par le Scheduler."""

    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    RETRY_WAIT = "retry-wait"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"

    @property
    def terminal(self) -> bool:
        return self in {
            SchedulerTaskState.COMPLETED,
            SchedulerTaskState.FAILED,
            SchedulerTaskState.CANCELLED,
            SchedulerTaskState.TIMED_OUT,
        }


class SchedulerTaskDependencyKind(str, Enum):
    """Condition exigée sur une tâche prédécesseure."""

    SUCCEEDED = "succeeded"
    TERMINAL = "terminal"


class SchedulerTaskAttemptState(str, Enum):
    """État d'une tentative d'exécution concrète."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"

    @property
    def terminal(self) -> bool:
        return self is not SchedulerTaskAttemptState.RUNNING


_ALLOWED_TRANSITIONS: Mapping[SchedulerTaskState, frozenset[SchedulerTaskState]] = {
    SchedulerTaskState.PLANNED: frozenset(
        {SchedulerTaskState.READY, SchedulerTaskState.CANCELLED}
    ),
    SchedulerTaskState.READY: frozenset(
        {SchedulerTaskState.RUNNING, SchedulerTaskState.CANCELLED, SchedulerTaskState.TIMED_OUT}
    ),
    SchedulerTaskState.RUNNING: frozenset(
        {
            SchedulerTaskState.PAUSED,
            SchedulerTaskState.RETRY_WAIT,
            SchedulerTaskState.COMPLETED,
            SchedulerTaskState.FAILED,
            SchedulerTaskState.CANCELLED,
            SchedulerTaskState.TIMED_OUT,
        }
    ),
    SchedulerTaskState.PAUSED: frozenset(
        {SchedulerTaskState.READY, SchedulerTaskState.CANCELLED, SchedulerTaskState.TIMED_OUT}
    ),
    SchedulerTaskState.RETRY_WAIT: frozenset(
        {SchedulerTaskState.READY, SchedulerTaskState.CANCELLED, SchedulerTaskState.TIMED_OUT}
    ),
    SchedulerTaskState.COMPLETED: frozenset(),
    SchedulerTaskState.FAILED: frozenset(),
    SchedulerTaskState.CANCELLED: frozenset(),
    SchedulerTaskState.TIMED_OUT: frozenset(),
}


@dataclass(frozen=True, slots=True)
class SchedulerTaskDependency:
    """Dépendance typée vers une autre tâche du même graphe Scheduler."""

    task_ref: str
    kind: SchedulerTaskDependencyKind

    def __post_init__(self) -> None:
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")

    def satisfied_by(self, state: SchedulerTaskState) -> bool:
        if self.kind is SchedulerTaskDependencyKind.SUCCEEDED:
            return state is SchedulerTaskState.COMPLETED
        return state.terminal


@dataclass(frozen=True, slots=True)
class SchedulerTaskTransition:
    """Preuve immuable d'une transition décidée par le Scheduler."""

    transition_ref: str
    task_ref: str
    from_state: SchedulerTaskState
    to_state: SchedulerTaskState
    state_version: int
    occurred_at: str
    actor_ref: str
    cause_ref: str
    transition_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("transition_ref", self.transition_ref, "scheduler-transition:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_positive_int("state_version", self.state_version)
        _require_utc("occurred_at", self.occurred_at)
        _require_typed_ref("actor_ref", self.actor_ref)
        _require_typed_ref("cause_ref", self.cause_ref)
        _require_sha256("transition_digest", self.transition_digest)
        if self.to_state not in _ALLOWED_TRANSITIONS[self.from_state]:
            raise SchedulerTaskModelError(
                f"transition interdite: {self.from_state.value} -> {self.to_state.value}"
            )
        expected = _transition_digest(
            task_ref=self.task_ref,
            from_state=self.from_state,
            to_state=self.to_state,
            state_version=self.state_version,
            occurred_at=self.occurred_at,
            actor_ref=self.actor_ref,
            cause_ref=self.cause_ref,
        )
        if expected != self.transition_digest:
            raise SchedulerTaskModelError("transition_digest incohérent")
        expected_ref = f"scheduler-transition:{_bare_digest(expected)[:24]}"
        if self.transition_ref != expected_ref:
            raise SchedulerTaskModelError("transition_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        task_ref: str,
        from_state: SchedulerTaskState,
        to_state: SchedulerTaskState,
        state_version: int,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskTransition:
        digest = _transition_digest(
            task_ref=task_ref,
            from_state=from_state,
            to_state=to_state,
            state_version=state_version,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        return cls(
            transition_ref=f"scheduler-transition:{_bare_digest(digest)[:24]}",
            task_ref=task_ref,
            from_state=from_state,
            to_state=to_state,
            state_version=state_version,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
            transition_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskAttempt:
    """Tentative concrète d'un handler pour une tâche."""

    attempt_ref: str
    task_ref: str
    number: int
    state: SchedulerTaskAttemptState
    handler_ref: str
    capability_ref: str
    contract_version: int
    started_at: str
    deadline_at: str
    finished_at: str = ""
    result_ref: str = ""
    failure_ref: str = ""

    def __post_init__(self) -> None:
        _require_typed_ref("attempt_ref", self.attempt_ref, "scheduler-attempt:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_positive_int("number", self.number)
        _require_typed_ref("handler_ref", self.handler_ref, "handler:")
        _require_typed_ref("capability_ref", self.capability_ref, "capability:")
        _require_positive_int("contract_version", self.contract_version)
        _require_utc("started_at", self.started_at)
        _require_utc("deadline_at", self.deadline_at)
        if self.state is SchedulerTaskAttemptState.RUNNING:
            if self.finished_at or self.result_ref or self.failure_ref:
                raise SchedulerTaskModelError(
                    "une tentative running ne porte ni fin, résultat ou échec"
                )
            return
        _require_utc("finished_at", self.finished_at)
        if self.state is SchedulerTaskAttemptState.SUCCEEDED:
            _require_typed_ref("result_ref", self.result_ref, "scheduler-task-result:")
            if self.failure_ref:
                raise SchedulerTaskModelError("une tentative réussie ne porte pas failure_ref")
        elif self.state is SchedulerTaskAttemptState.FAILED:
            _require_typed_ref("failure_ref", self.failure_ref, "scheduler-task-failure:")
            if self.result_ref:
                raise SchedulerTaskModelError("une tentative échouée ne porte pas result_ref")
        elif self.result_ref or self.failure_ref:
            raise SchedulerTaskModelError(
                "une tentative annulée ou expirée ne porte ni résultat ni échec métier"
            )

    @classmethod
    def start(
        cls,
        *,
        task_ref: str,
        number: int,
        handler_ref: str,
        capability_ref: str,
        contract_version: int,
        started_at: str,
        deadline_at: str,
    ) -> SchedulerTaskAttempt:
        digest = _length_prefixed_digest(
            (
                ("task_ref", task_ref),
                ("number", number),
                ("handler_ref", handler_ref),
                ("capability_ref", capability_ref),
                ("contract_version", contract_version),
                ("started_at", started_at),
                ("deadline_at", deadline_at),
            )
        )
        return cls(
            attempt_ref=f"scheduler-attempt:{digest[:24]}",
            task_ref=task_ref,
            number=number,
            state=SchedulerTaskAttemptState.RUNNING,
            handler_ref=handler_ref,
            capability_ref=capability_ref,
            contract_version=contract_version,
            started_at=started_at,
            deadline_at=deadline_at,
        )

    def succeeded(self, *, result_ref: str, finished_at: str) -> SchedulerTaskAttempt:
        if self.state is not SchedulerTaskAttemptState.RUNNING:
            raise SchedulerTaskModelError("seule une tentative running peut réussir")
        return replace(
            self,
            state=SchedulerTaskAttemptState.SUCCEEDED,
            result_ref=result_ref,
            finished_at=finished_at,
        )

    def failed(self, *, failure_ref: str, finished_at: str) -> SchedulerTaskAttempt:
        if self.state is not SchedulerTaskAttemptState.RUNNING:
            raise SchedulerTaskModelError("seule une tentative running peut échouer")
        return replace(
            self,
            state=SchedulerTaskAttemptState.FAILED,
            failure_ref=failure_ref,
            finished_at=finished_at,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskResult:
    """Résultat typé produit par une tentative réussie."""

    result_ref: str
    task_ref: str
    attempt_ref: str
    result_type_ref: str
    completed_at: str
    evidence_refs: tuple[str, ...]
    result_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("result_ref", self.result_ref, "scheduler-task-result:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("attempt_ref", self.attempt_ref, "scheduler-attempt:")
        _require_typed_ref("result_type_ref", self.result_type_ref, "result-type:")
        _require_utc("completed_at", self.completed_at)
        refs = _validated_refs("evidence_refs", self.evidence_refs, allow_empty=True)
        object.__setattr__(self, "evidence_refs", refs)
        _require_sha256("result_digest", self.result_digest)
        expected = _task_result_digest(
            task_ref=self.task_ref,
            attempt_ref=self.attempt_ref,
            result_type_ref=self.result_type_ref,
            completed_at=self.completed_at,
            evidence_refs=self.evidence_refs,
        )
        if expected != self.result_digest:
            raise SchedulerTaskModelError("result_digest incohérent")
        if self.result_ref != f"scheduler-task-result:{_bare_digest(expected)[:24]}":
            raise SchedulerTaskModelError("result_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        task_ref: str,
        attempt_ref: str,
        result_type_ref: str,
        completed_at: str,
        evidence_refs: Sequence[str] = (),
    ) -> SchedulerTaskResult:
        refs = tuple(evidence_refs)
        digest = _task_result_digest(
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            result_type_ref=result_type_ref,
            completed_at=completed_at,
            evidence_refs=refs,
        )
        return cls(
            result_ref=f"scheduler-task-result:{_bare_digest(digest)[:24]}",
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            result_type_ref=result_type_ref,
            completed_at=completed_at,
            evidence_refs=refs,
            result_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskFailure:
    """Échec typé transmis au Scheduler pour décision de reprise."""

    failure_ref: str
    task_ref: str
    attempt_ref: str
    error_type: str
    message: str
    retryable: bool
    failed_at: str
    evidence_refs: tuple[str, ...]
    failure_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("failure_ref", self.failure_ref, "scheduler-task-failure:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("attempt_ref", self.attempt_ref, "scheduler-attempt:")
        _require_non_empty("error_type", self.error_type)
        _require_non_empty("message", self.message)
        if not isinstance(self.retryable, bool):
            raise SchedulerTaskModelError("retryable doit être booléen")
        _require_utc("failed_at", self.failed_at)
        refs = _validated_refs("evidence_refs", self.evidence_refs, allow_empty=True)
        object.__setattr__(self, "evidence_refs", refs)
        _require_sha256("failure_digest", self.failure_digest)
        expected = _task_failure_digest(
            task_ref=self.task_ref,
            attempt_ref=self.attempt_ref,
            error_type=self.error_type,
            message=self.message,
            retryable=self.retryable,
            failed_at=self.failed_at,
            evidence_refs=self.evidence_refs,
        )
        if expected != self.failure_digest:
            raise SchedulerTaskModelError("failure_digest incohérent")
        if self.failure_ref != f"scheduler-task-failure:{_bare_digest(expected)[:24]}":
            raise SchedulerTaskModelError("failure_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        task_ref: str,
        attempt_ref: str,
        error_type: str,
        message: str,
        retryable: bool,
        failed_at: str,
        evidence_refs: Sequence[str] = (),
    ) -> SchedulerTaskFailure:
        refs = tuple(evidence_refs)
        digest = _task_failure_digest(
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            error_type=error_type,
            message=message,
            retryable=retryable,
            failed_at=failed_at,
            evidence_refs=refs,
        )
        return cls(
            failure_ref=f"scheduler-task-failure:{_bare_digest(digest)[:24]}",
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            error_type=error_type,
            message=message,
            retryable=retryable,
            failed_at=failed_at,
            evidence_refs=refs,
            failure_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTask:
    """Unité de travail immuable gouvernée par le Scheduler canonique."""

    task_ref: str
    command_ref: str
    task_kind_ref: str
    capability_ref: str
    contract_version: int
    state: SchedulerTaskState
    state_version: int
    initial_priority: int
    effective_priority: int
    max_attempts: int
    attempt_count: int
    created_at: str
    updated_at: str
    parent_task_ref: str
    dependencies: tuple[SchedulerTaskDependency, ...]
    context_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    task_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("task_kind_ref", self.task_kind_ref, "task-kind:")
        _require_typed_ref("capability_ref", self.capability_ref, "capability:")
        _require_positive_int("contract_version", self.contract_version)
        _require_positive_int("state_version", self.state_version)
        _require_int_range("initial_priority", self.initial_priority, 0, 100)
        _require_int_range("effective_priority", self.effective_priority, 0, 100)
        _require_positive_int("max_attempts", self.max_attempts)
        _require_non_negative_int("attempt_count", self.attempt_count)
        if self.attempt_count > self.max_attempts:
            raise SchedulerTaskModelError("attempt_count dépasse max_attempts")
        _require_utc("created_at", self.created_at)
        _require_utc("updated_at", self.updated_at)
        if self.parent_task_ref:
            _require_typed_ref("parent_task_ref", self.parent_task_ref, "scheduler-task:")
            if self.parent_task_ref == self.task_ref:
                raise SchedulerTaskModelError("une tâche ne peut être son propre parent")
        deps = tuple(self.dependencies)
        if len({dep.task_ref for dep in deps}) != len(deps):
            raise SchedulerTaskModelError("dependencies contient un prédécesseur dupliqué")
        if any(dep.task_ref == self.task_ref for dep in deps):
            raise SchedulerTaskModelError("une tâche ne peut dépendre d'elle-même")
        object.__setattr__(self, "dependencies", deps)
        object.__setattr__(
            self,
            "context_refs",
            _validated_refs("context_refs", self.context_refs, allow_empty=True),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _validated_refs("evidence_refs", self.evidence_refs, allow_empty=True),
        )
        if self.state is SchedulerTaskState.RUNNING and self.attempt_count == 0:
            raise SchedulerTaskModelError("une tâche running exige une tentative")
        if self.state is SchedulerTaskState.COMPLETED and self.attempt_count == 0:
            raise SchedulerTaskModelError("une tâche completed exige une tentative")
        _require_sha256("task_digest", self.task_digest)
        expected = _task_digest(
            task_ref=self.task_ref,
            command_ref=self.command_ref,
            task_kind_ref=self.task_kind_ref,
            capability_ref=self.capability_ref,
            contract_version=self.contract_version,
            state=self.state,
            state_version=self.state_version,
            initial_priority=self.initial_priority,
            effective_priority=self.effective_priority,
            max_attempts=self.max_attempts,
            attempt_count=self.attempt_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
            parent_task_ref=self.parent_task_ref,
            dependencies=self.dependencies,
            context_refs=self.context_refs,
            evidence_refs=self.evidence_refs,
        )
        if expected != self.task_digest:
            raise SchedulerTaskModelError("task_digest incohérent")

    @classmethod
    def plan(
        cls,
        *,
        task_ref: str,
        command_ref: str,
        task_kind_ref: str,
        capability_ref: str,
        contract_version: int,
        priority: int,
        max_attempts: int,
        created_at: str,
        parent_task_ref: str = "",
        dependencies: Sequence[SchedulerTaskDependency] = (),
        context_refs: Sequence[str] = (),
        evidence_refs: Sequence[str] = (),
    ) -> SchedulerTask:
        values = dict(
            task_ref=task_ref,
            command_ref=command_ref,
            task_kind_ref=task_kind_ref,
            capability_ref=capability_ref,
            contract_version=contract_version,
            state=SchedulerTaskState.PLANNED,
            state_version=1,
            initial_priority=priority,
            effective_priority=priority,
            max_attempts=max_attempts,
            attempt_count=0,
            created_at=created_at,
            updated_at=created_at,
            parent_task_ref=parent_task_ref,
            dependencies=tuple(dependencies),
            context_refs=tuple(context_refs),
            evidence_refs=tuple(evidence_refs),
        )
        return cls(task_digest=_task_digest(**values), **values)

    def dependencies_satisfied(
        self,
        states: Mapping[str, SchedulerTaskState],
    ) -> bool:
        return all(
            dependency.task_ref in states
            and dependency.satisfied_by(states[dependency.task_ref])
            for dependency in self.dependencies
        )

    def mark_ready(
        self,
        *,
        dependency_states: Mapping[str, SchedulerTaskState],
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskMutation:
        if self.state not in {
            SchedulerTaskState.PLANNED,
            SchedulerTaskState.PAUSED,
            SchedulerTaskState.RETRY_WAIT,
        }:
            raise SchedulerTaskModelError("seule une tâche planned/paused/retry-wait devient ready")
        if not self.dependencies_satisfied(dependency_states):
            raise SchedulerTaskModelError("les dépendances ne sont pas satisfaites")
        return self._transition(
            to_state=SchedulerTaskState.READY,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )

    def start_attempt(
        self,
        *,
        handler_ref: str,
        contract_version: int,
        started_at: str,
        deadline_at: str,
        actor_ref: str,
        cause_ref: str,
        effective_priority: int | None = None,
    ) -> SchedulerTaskAttemptStart:
        if self.state is not SchedulerTaskState.READY:
            raise SchedulerTaskModelError("seule une tâche ready peut démarrer")
        if self.attempt_count >= self.max_attempts:
            raise SchedulerTaskModelError("budget de tentatives épuisé")
        if contract_version != self.contract_version:
            raise SchedulerTaskModelError(
                "la version du handler doit correspondre à la version de capacité de la tâche"
            )
        next_effective_priority = (
            self.effective_priority
            if effective_priority is None
            else effective_priority
        )
        _require_int_range(
            "effective_priority", next_effective_priority, 0, 100
        )
        next_attempt_count = self.attempt_count + 1
        transition = SchedulerTaskTransition.create(
            task_ref=self.task_ref,
            from_state=self.state,
            to_state=SchedulerTaskState.RUNNING,
            state_version=self.state_version + 1,
            occurred_at=started_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        task = self._rebuild(
            state=SchedulerTaskState.RUNNING,
            state_version=self.state_version + 1,
            effective_priority=next_effective_priority,
            attempt_count=next_attempt_count,
            updated_at=started_at,
        )
        attempt = SchedulerTaskAttempt.start(
            task_ref=self.task_ref,
            number=next_attempt_count,
            handler_ref=handler_ref,
            capability_ref=self.capability_ref,
            contract_version=contract_version,
            started_at=started_at,
            deadline_at=deadline_at,
        )
        return SchedulerTaskAttemptStart(task=task, attempt=attempt, transition=transition)

    def complete_attempt(
        self,
        *,
        attempt: SchedulerTaskAttempt,
        result: SchedulerTaskResult,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskAttemptCompletion:
        _validate_running_attempt(self, attempt)
        if result.task_ref != self.task_ref or result.attempt_ref != attempt.attempt_ref:
            raise SchedulerTaskModelError("le résultat ne correspond pas à la tentative")
        if result.completed_at != occurred_at:
            raise SchedulerTaskModelError(
                "l'horodatage du résultat doit correspondre à la transition"
            )
        completed_attempt = attempt.succeeded(
            result_ref=result.result_ref,
            finished_at=occurred_at,
        )
        mutation = self._transition(
            to_state=SchedulerTaskState.COMPLETED,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        return SchedulerTaskAttemptCompletion(
            task=mutation.task,
            attempt=completed_attempt,
            result=result,
            transition=mutation.transition,
        )

    def fail_attempt(
        self,
        *,
        attempt: SchedulerTaskAttempt,
        failure: SchedulerTaskFailure,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskAttemptFailureOutcome:
        _validate_running_attempt(self, attempt)
        if failure.task_ref != self.task_ref or failure.attempt_ref != attempt.attempt_ref:
            raise SchedulerTaskModelError("l'échec ne correspond pas à la tentative")
        if failure.failed_at != occurred_at:
            raise SchedulerTaskModelError(
                "l'horodatage de l'échec doit correspondre à la transition"
            )
        failed_attempt = attempt.failed(
            failure_ref=failure.failure_ref,
            finished_at=occurred_at,
        )
        retry_allowed = failure.retryable and self.attempt_count < self.max_attempts
        target = (
            SchedulerTaskState.RETRY_WAIT if retry_allowed else SchedulerTaskState.FAILED
        )
        mutation = self._transition(
            to_state=target,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        return SchedulerTaskAttemptFailureOutcome(
            task=mutation.task,
            attempt=failed_attempt,
            failure=failure,
            retry_scheduled=retry_allowed,
            transition=mutation.transition,
        )

    def move_to(
        self,
        *,
        to_state: SchedulerTaskState,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskMutation:
        if to_state in {
            SchedulerTaskState.RUNNING,
            SchedulerTaskState.COMPLETED,
            SchedulerTaskState.FAILED,
            SchedulerTaskState.RETRY_WAIT,
        }:
            raise SchedulerTaskModelError(
                "cette transition exige une méthode d'exécution spécialisée"
            )
        return self._transition(
            to_state=to_state,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )

    def _transition(
        self,
        *,
        to_state: SchedulerTaskState,
        occurred_at: str,
        actor_ref: str,
        cause_ref: str,
    ) -> SchedulerTaskMutation:
        transition = SchedulerTaskTransition.create(
            task_ref=self.task_ref,
            from_state=self.state,
            to_state=to_state,
            state_version=self.state_version + 1,
            occurred_at=occurred_at,
            actor_ref=actor_ref,
            cause_ref=cause_ref,
        )
        task = self._rebuild(
            state=to_state,
            state_version=self.state_version + 1,
            updated_at=occurred_at,
        )
        return SchedulerTaskMutation(task=task, transition=transition)

    def _rebuild(self, **changes: object) -> SchedulerTask:
        values = {
            "task_ref": self.task_ref,
            "command_ref": self.command_ref,
            "task_kind_ref": self.task_kind_ref,
            "capability_ref": self.capability_ref,
            "contract_version": self.contract_version,
            "state": self.state,
            "state_version": self.state_version,
            "initial_priority": self.initial_priority,
            "effective_priority": self.effective_priority,
            "max_attempts": self.max_attempts,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "parent_task_ref": self.parent_task_ref,
            "dependencies": self.dependencies,
            "context_refs": self.context_refs,
            "evidence_refs": self.evidence_refs,
        }
        values.update(changes)
        return SchedulerTask(task_digest=_task_digest(**values), **values)  # type: ignore[arg-type]


@dataclass(frozen=True, slots=True)
class SchedulerTaskMutation:
    task: SchedulerTask
    transition: SchedulerTaskTransition

    def __post_init__(self) -> None:
        if self.task.task_ref != self.transition.task_ref:
            raise SchedulerTaskModelError("mutation et transition portent des tâches différentes")
        if self.task.state is not self.transition.to_state:
            raise SchedulerTaskModelError("mutation et transition portent des états différents")
        if self.task.state_version != self.transition.state_version:
            raise SchedulerTaskModelError("mutation et transition portent des versions différentes")


@dataclass(frozen=True, slots=True)
class SchedulerTaskAttemptStart:
    task: SchedulerTask
    attempt: SchedulerTaskAttempt
    transition: SchedulerTaskTransition

    def __post_init__(self) -> None:
        _validate_attempt_bundle(self.task, self.attempt, self.transition)
        if self.task.state is not SchedulerTaskState.RUNNING:
            raise SchedulerTaskModelError("le démarrage doit produire une tâche running")


@dataclass(frozen=True, slots=True)
class SchedulerTaskAttemptCompletion:
    task: SchedulerTask
    attempt: SchedulerTaskAttempt
    result: SchedulerTaskResult
    transition: SchedulerTaskTransition

    def __post_init__(self) -> None:
        _validate_attempt_bundle(self.task, self.attempt, self.transition)
        if self.task.state is not SchedulerTaskState.COMPLETED:
            raise SchedulerTaskModelError("la réussite doit produire une tâche completed")
        if self.attempt.state is not SchedulerTaskAttemptState.SUCCEEDED:
            raise SchedulerTaskModelError("la tentative doit être succeeded")
        if self.attempt.result_ref != self.result.result_ref:
            raise SchedulerTaskModelError("la tentative ne référence pas son résultat")


@dataclass(frozen=True, slots=True)
class SchedulerTaskAttemptFailureOutcome:
    task: SchedulerTask
    attempt: SchedulerTaskAttempt
    failure: SchedulerTaskFailure
    retry_scheduled: bool
    transition: SchedulerTaskTransition

    def __post_init__(self) -> None:
        _validate_attempt_bundle(self.task, self.attempt, self.transition)
        if self.attempt.state is not SchedulerTaskAttemptState.FAILED:
            raise SchedulerTaskModelError("la tentative doit être failed")
        if self.attempt.failure_ref != self.failure.failure_ref:
            raise SchedulerTaskModelError("la tentative ne référence pas son échec")
        expected_state = (
            SchedulerTaskState.RETRY_WAIT
            if self.retry_scheduled
            else SchedulerTaskState.FAILED
        )
        if self.task.state is not expected_state:
            raise SchedulerTaskModelError("l'état de tâche ne correspond pas à la décision de reprise")


def _validate_running_attempt(task: SchedulerTask, attempt: SchedulerTaskAttempt) -> None:
    if task.state is not SchedulerTaskState.RUNNING:
        raise SchedulerTaskModelError("la tâche doit être running")
    if attempt.state is not SchedulerTaskAttemptState.RUNNING:
        raise SchedulerTaskModelError("la tentative doit être running")
    if attempt.task_ref != task.task_ref or attempt.number != task.attempt_count:
        raise SchedulerTaskModelError("la tentative ne correspond pas à la tâche")


def _validate_attempt_bundle(
    task: SchedulerTask,
    attempt: SchedulerTaskAttempt,
    transition: SchedulerTaskTransition,
) -> None:
    if task.task_ref != attempt.task_ref or task.task_ref != transition.task_ref:
        raise SchedulerTaskModelError("bundle de tentative non corrélé")
    if task.state is not transition.to_state:
        raise SchedulerTaskModelError("bundle de tentative avec état divergent")
    if task.state_version != transition.state_version:
        raise SchedulerTaskModelError("bundle de tentative avec version divergente")


def _task_digest(**values: object) -> str:
    dependencies = values.pop("dependencies")
    context_refs = values.pop("context_refs")
    evidence_refs = values.pop("evidence_refs")
    state = values["state"]
    assert isinstance(state, SchedulerTaskState)
    parts: list[tuple[str, object]] = [
        ("task_ref", values["task_ref"]),
        ("command_ref", values["command_ref"]),
        ("task_kind_ref", values["task_kind_ref"]),
        ("capability_ref", values["capability_ref"]),
        ("contract_version", values["contract_version"]),
        ("state", state.value),
        ("state_version", values["state_version"]),
        ("initial_priority", values["initial_priority"]),
        ("effective_priority", values["effective_priority"]),
        ("max_attempts", values["max_attempts"]),
        ("attempt_count", values["attempt_count"]),
        ("created_at", values["created_at"]),
        ("updated_at", values["updated_at"]),
        ("parent_task_ref", values["parent_task_ref"]),
    ]
    assert isinstance(dependencies, tuple)
    for dependency in dependencies:
        assert isinstance(dependency, SchedulerTaskDependency)
        parts.extend(
            (
                ("dependency_task_ref", dependency.task_ref),
                ("dependency_kind", dependency.kind.value),
            )
        )
    assert isinstance(context_refs, tuple)
    parts.extend(("context_ref", value) for value in context_refs)
    assert isinstance(evidence_refs, tuple)
    parts.extend(("evidence_ref", value) for value in evidence_refs)
    return "sha256:" + _length_prefixed_digest(parts)


def _transition_digest(
    *,
    task_ref: str,
    from_state: SchedulerTaskState,
    to_state: SchedulerTaskState,
    state_version: int,
    occurred_at: str,
    actor_ref: str,
    cause_ref: str,
) -> str:
    return "sha256:" + _length_prefixed_digest(
        (
            ("task_ref", task_ref),
            ("from_state", from_state.value),
            ("to_state", to_state.value),
            ("state_version", state_version),
            ("occurred_at", occurred_at),
            ("actor_ref", actor_ref),
            ("cause_ref", cause_ref),
        )
    )


def _task_result_digest(
    *,
    task_ref: str,
    attempt_ref: str,
    result_type_ref: str,
    completed_at: str,
    evidence_refs: Sequence[str],
) -> str:
    parts: list[tuple[str, object]] = [
        ("task_ref", task_ref),
        ("attempt_ref", attempt_ref),
        ("result_type_ref", result_type_ref),
        ("completed_at", completed_at),
    ]
    parts.extend(("evidence_ref", value) for value in evidence_refs)
    return "sha256:" + _length_prefixed_digest(parts)


def _task_failure_digest(
    *,
    task_ref: str,
    attempt_ref: str,
    error_type: str,
    message: str,
    retryable: bool,
    failed_at: str,
    evidence_refs: Sequence[str],
) -> str:
    parts: list[tuple[str, object]] = [
        ("task_ref", task_ref),
        ("attempt_ref", attempt_ref),
        ("error_type", error_type),
        ("message", message),
        ("retryable", retryable),
        ("failed_at", failed_at),
    ]
    parts.extend(("evidence_ref", value) for value in evidence_refs)
    return "sha256:" + _length_prefixed_digest(parts)


def _length_prefixed_digest(parts: Sequence[tuple[str, object]]) -> str:
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
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SchedulerTaskModelError("les flottants de digest doivent être finis")
        return value.hex()
    if isinstance(value, (str, int)):
        return str(value)
    raise SchedulerTaskModelError(
        f"type scalaire non pris en charge: {type(value).__name__}"
    )


def _validated_refs(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    result = tuple(values)
    if not allow_empty and not result:
        raise SchedulerTaskModelError(f"{name} ne doit pas être vide")
    if len(set(result)) != len(result):
        raise SchedulerTaskModelError(f"{name} contient un doublon")
    for value in result:
        _require_typed_ref(name, value)
    return result


def _require_non_empty(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SchedulerTaskModelError(f"{name} doit être une chaîne non vide")


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    _require_non_empty(name, value)
    text = str(value)
    if _TYPED_REF_RE.fullmatch(text) is None:
        raise SchedulerTaskModelError(f"{name} doit être une référence typée")
    if prefix and not text.startswith(prefix):
        raise SchedulerTaskModelError(f"{name} doit commencer par {prefix}")


def _require_utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise SchedulerTaskModelError(f"{name} doit être un horodatage UTC finissant par Z")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SchedulerTaskModelError(f"{name} doit être un SHA-256 minuscule")


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SchedulerTaskModelError(f"{name} doit être un entier strictement positif")


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SchedulerTaskModelError(f"{name} doit être un entier positif ou nul")


def _require_int_range(name: str, value: object, minimum: int, maximum: int) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise SchedulerTaskModelError(
            f"{name} doit être compris entre {minimum} et {maximum}"
        )


__all__ = (
    "SchedulerTask",
    "SchedulerTaskAttempt",
    "SchedulerTaskAttemptCompletion",
    "SchedulerTaskAttemptFailureOutcome",
    "SchedulerTaskAttemptStart",
    "SchedulerTaskAttemptState",
    "SchedulerTaskDependency",
    "SchedulerTaskDependencyKind",
    "SchedulerTaskFailure",
    "SchedulerTaskModelError",
    "SchedulerTaskMutation",
    "SchedulerTaskResult",
    "SchedulerTaskState",
    "SchedulerTaskTransition",
)
