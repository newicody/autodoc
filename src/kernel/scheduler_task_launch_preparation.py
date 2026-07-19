"""Transactional application of one admitted Scheduler task launch.

This module bridges the pure admission plan with a durable transaction port. It
resolves the exact handler contract, creates the immutable running task and
attempt, charges the bounded command budget, commits the whole launch through
one injected authority, and returns a typed launch ticket.

It deliberately does not instantiate or execute the handler. Lifecycle notices
``CREATED`` and ``STARTED`` belong to the following executor boundary, after a
real handler instance exists and the durable launch commit succeeded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import re
from typing import Generic, Protocol, TypeVar, runtime_checkable

from .scheduler_handler_catalog import (
    SchedulerHandlerBinding,
    SchedulerHandlerCatalog,
)
from .scheduler_task_admission import (
    SchedulerAdmissionStatus,
    SchedulerBudgetCharge,
    SchedulerCommandExecutionBudget,
    SchedulerResourceReservation,
    SchedulerTaskAdmissionCandidate,
    SchedulerTaskAdmissionDecision,
    SchedulerTaskAdmissionPlan,
)
from .scheduler_task_model import (
    SchedulerTask,
    SchedulerTaskAttempt,
    SchedulerTaskAttemptStart,
    SchedulerTaskState,
    SchedulerTaskTransition,
)


CommandT = TypeVar("CommandT")

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

SCHEDULER_TASK_LAUNCH_COMMIT_SCHEMA = "missipy.scheduler.task_launch_commit.v1"
SCHEDULER_HANDLER_LAUNCH_TICKET_SCHEMA = "missipy.scheduler.handler_launch_ticket.v1"


class SchedulerTaskLaunchPreparationError(RuntimeError):
    """Raised when an admission plan cannot become one durable launch ticket."""


@dataclass(frozen=True, slots=True)
class SchedulerCommandBudgetMutation:
    """Typed before/after proof for one bounded command-budget charge."""

    budget_ref: str
    command_ref: str
    scheduler_steps_before: int
    scheduler_steps_after: int
    specialist_visits_before: int
    specialist_visits_after: int
    charge: SchedulerBudgetCharge
    mutation_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref("budget_ref", self.budget_ref, "scheduler-command-budget:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_non_negative_int("scheduler_steps_before", self.scheduler_steps_before)
        _require_non_negative_int("scheduler_steps_after", self.scheduler_steps_after)
        _require_non_negative_int(
            "specialist_visits_before", self.specialist_visits_before
        )
        _require_non_negative_int(
            "specialist_visits_after", self.specialist_visits_after
        )
        if self.scheduler_steps_after != (
            self.scheduler_steps_before + self.charge.scheduler_steps
        ):
            raise SchedulerTaskLaunchPreparationError(
                "scheduler_steps_after ne correspond pas à la charge"
            )
        if self.specialist_visits_after != (
            self.specialist_visits_before + self.charge.specialist_visits
        ):
            raise SchedulerTaskLaunchPreparationError(
                "specialist_visits_after ne correspond pas à la charge"
            )
        _require_sha256("mutation_digest", self.mutation_digest)
        expected = _budget_mutation_digest(
            budget_ref=self.budget_ref,
            command_ref=self.command_ref,
            scheduler_steps_before=self.scheduler_steps_before,
            scheduler_steps_after=self.scheduler_steps_after,
            specialist_visits_before=self.specialist_visits_before,
            specialist_visits_after=self.specialist_visits_after,
            charge=self.charge,
        )
        if self.mutation_digest != expected:
            raise SchedulerTaskLaunchPreparationError("mutation_digest incohérent")

    @classmethod
    def create(
        cls,
        *,
        budget: SchedulerCommandExecutionBudget,
        charge: SchedulerBudgetCharge,
    ) -> SchedulerCommandBudgetMutation:
        refusal = budget.refusal_for(charge)
        if refusal is not None:
            raise SchedulerTaskLaunchPreparationError(
                f"budget de commande insuffisant: {refusal.value}"
            )
        values = dict(
            budget_ref=budget.budget_ref,
            command_ref=budget.command_ref,
            scheduler_steps_before=budget.consumed_scheduler_steps,
            scheduler_steps_after=(
                budget.consumed_scheduler_steps + charge.scheduler_steps
            ),
            specialist_visits_before=budget.consumed_specialist_visits,
            specialist_visits_after=(
                budget.consumed_specialist_visits + charge.specialist_visits
            ),
            charge=charge,
        )
        return cls(
            **values,
            mutation_digest=_budget_mutation_digest(**values),
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskLaunchCommit:
    """Receipt returned only after one atomic durable launch transaction."""

    schema: str
    transaction_ref: str
    scheduler_ref: str
    command_ref: str
    task_ref: str
    attempt_ref: str
    reservation_ref: str
    admission_plan_digest: str
    task_state_version: int
    scheduler_steps_after: int
    specialist_visits_after: int
    committed_at: str
    commit_digest: str

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_TASK_LAUNCH_COMMIT_SCHEMA:
            raise SchedulerTaskLaunchPreparationError(
                "unsupported Scheduler task launch commit schema"
            )
        _require_typed_ref("transaction_ref", self.transaction_ref, "scheduler-launch-transaction:")
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("attempt_ref", self.attempt_ref, "scheduler-attempt:")
        _require_typed_ref(
            "reservation_ref", self.reservation_ref, "scheduler-reservation:"
        )
        _require_sha256("admission_plan_digest", self.admission_plan_digest)
        _require_positive_int("task_state_version", self.task_state_version)
        _require_non_negative_int("scheduler_steps_after", self.scheduler_steps_after)
        _require_non_negative_int(
            "specialist_visits_after", self.specialist_visits_after
        )
        _parse_utc("committed_at", self.committed_at)
        _require_sha256("commit_digest", self.commit_digest)
        expected = _launch_commit_digest(
            scheduler_ref=self.scheduler_ref,
            command_ref=self.command_ref,
            task_ref=self.task_ref,
            attempt_ref=self.attempt_ref,
            reservation_ref=self.reservation_ref,
            admission_plan_digest=self.admission_plan_digest,
            task_state_version=self.task_state_version,
            scheduler_steps_after=self.scheduler_steps_after,
            specialist_visits_after=self.specialist_visits_after,
            committed_at=self.committed_at,
        )
        if self.commit_digest != expected:
            raise SchedulerTaskLaunchPreparationError("commit_digest incohérent")
        expected_ref = f"scheduler-launch-transaction:{_bare_digest(expected)[:24]}"
        if self.transaction_ref != expected_ref:
            raise SchedulerTaskLaunchPreparationError("transaction_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        scheduler_ref: str,
        command_ref: str,
        task_ref: str,
        attempt_ref: str,
        reservation_ref: str,
        admission_plan_digest: str,
        task_state_version: int,
        scheduler_steps_after: int,
        specialist_visits_after: int,
        committed_at: str,
    ) -> SchedulerTaskLaunchCommit:
        digest = _launch_commit_digest(
            scheduler_ref=scheduler_ref,
            command_ref=command_ref,
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            reservation_ref=reservation_ref,
            admission_plan_digest=admission_plan_digest,
            task_state_version=task_state_version,
            scheduler_steps_after=scheduler_steps_after,
            specialist_visits_after=specialist_visits_after,
            committed_at=committed_at,
        )
        return cls(
            schema=SCHEDULER_TASK_LAUNCH_COMMIT_SCHEMA,
            transaction_ref=f"scheduler-launch-transaction:{_bare_digest(digest)[:24]}",
            scheduler_ref=scheduler_ref,
            command_ref=command_ref,
            task_ref=task_ref,
            attempt_ref=attempt_ref,
            reservation_ref=reservation_ref,
            admission_plan_digest=admission_plan_digest,
            task_state_version=task_state_version,
            scheduler_steps_after=scheduler_steps_after,
            specialist_visits_after=specialist_visits_after,
            committed_at=committed_at,
            commit_digest=digest,
        )


@runtime_checkable
class SchedulerTaskLaunchTransaction(Protocol):
    """Atomic authority port implemented later by the PostgreSQL adapter.

    One implementation must compare the expected task and budget versions,
    persist the resource reservation, budget charge, running task, attempt,
    transition and command ``running`` state in one transaction, or roll back
    every write.
    """

    def commit_launch(
        self,
        *,
        scheduler_ref: str,
        plan: SchedulerTaskAdmissionPlan,
        decision: SchedulerTaskAdmissionDecision,
        task_before: SchedulerTask,
        attempt_start: SchedulerTaskAttemptStart,
        budget_mutation: SchedulerCommandBudgetMutation,
        reservation: SchedulerResourceReservation,
        handler_binding: SchedulerHandlerBinding,
        committed_at: str,
    ) -> SchedulerTaskLaunchCommit: ...


@dataclass(frozen=True, slots=True)
class SchedulerHandlerLaunchTicket(Generic[CommandT]):
    """In-process ticket ready for handler construction, not execution."""

    schema: str
    ticket_ref: str
    scheduler_ref: str
    command: CommandT = field(repr=False, compare=False)
    handler_binding: SchedulerHandlerBinding
    task_before: SchedulerTask
    task_running: SchedulerTask
    attempt: SchedulerTaskAttempt
    transition: SchedulerTaskTransition
    reservation: SchedulerResourceReservation
    budget_mutation: SchedulerCommandBudgetMutation
    launch_commit: SchedulerTaskLaunchCommit
    ticket_digest: str

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_HANDLER_LAUNCH_TICKET_SCHEMA:
            raise SchedulerTaskLaunchPreparationError(
                "unsupported Scheduler handler launch ticket schema"
            )
        _require_typed_ref("ticket_ref", self.ticket_ref, "scheduler-handler-launch:")
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        command_ref = getattr(self.command, "command_ref", None)
        if command_ref != self.task_running.command_ref:
            raise SchedulerTaskLaunchPreparationError(
                "la commande et la tâche du ticket ne sont pas corrélées"
            )
        if self.task_before.task_ref != self.task_running.task_ref:
            raise SchedulerTaskLaunchPreparationError(
                "task_before et task_running divergent"
            )
        if self.task_before.state is not SchedulerTaskState.READY:
            raise SchedulerTaskLaunchPreparationError("task_before doit être ready")
        if self.task_running.state is not SchedulerTaskState.RUNNING:
            raise SchedulerTaskLaunchPreparationError("task_running doit être running")
        if self.attempt.task_ref != self.task_running.task_ref:
            raise SchedulerTaskLaunchPreparationError(
                "la tentative et la tâche du ticket divergent"
            )
        if self.transition.task_ref != self.task_running.task_ref:
            raise SchedulerTaskLaunchPreparationError(
                "la transition et la tâche du ticket divergent"
            )
        if self.handler_binding.handler_ref != self.attempt.handler_ref:
            raise SchedulerTaskLaunchPreparationError(
                "le handler du ticket diverge de la tentative"
            )
        if self.reservation.task_ref != self.task_running.task_ref:
            raise SchedulerTaskLaunchPreparationError(
                "la réservation et la tâche du ticket divergent"
            )
        if self.launch_commit.transaction_ref == "":
            raise SchedulerTaskLaunchPreparationError(
                "le ticket exige un commit transactionnel durable"
            )
        _require_sha256("ticket_digest", self.ticket_digest)
        expected = _ticket_digest(
            scheduler_ref=self.scheduler_ref,
            command_ref=self.task_running.command_ref,
            task_digest=self.task_running.task_digest,
            attempt_ref=self.attempt.attempt_ref,
            reservation_digest=self.reservation.reservation_digest,
            budget_mutation_digest=self.budget_mutation.mutation_digest,
            commit_digest=self.launch_commit.commit_digest,
            handler_ref=self.handler_binding.handler_ref,
        )
        if self.ticket_digest != expected:
            raise SchedulerTaskLaunchPreparationError("ticket_digest incohérent")
        expected_ref = f"scheduler-handler-launch:{_bare_digest(expected)[:24]}"
        if self.ticket_ref != expected_ref:
            raise SchedulerTaskLaunchPreparationError("ticket_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        scheduler_ref: str,
        command: CommandT,
        handler_binding: SchedulerHandlerBinding,
        task_before: SchedulerTask,
        attempt_start: SchedulerTaskAttemptStart,
        reservation: SchedulerResourceReservation,
        budget_mutation: SchedulerCommandBudgetMutation,
        launch_commit: SchedulerTaskLaunchCommit,
    ) -> SchedulerHandlerLaunchTicket[CommandT]:
        digest = _ticket_digest(
            scheduler_ref=scheduler_ref,
            command_ref=attempt_start.task.command_ref,
            task_digest=attempt_start.task.task_digest,
            attempt_ref=attempt_start.attempt.attempt_ref,
            reservation_digest=reservation.reservation_digest,
            budget_mutation_digest=budget_mutation.mutation_digest,
            commit_digest=launch_commit.commit_digest,
            handler_ref=handler_binding.handler_ref,
        )
        return cls(
            schema=SCHEDULER_HANDLER_LAUNCH_TICKET_SCHEMA,
            ticket_ref=f"scheduler-handler-launch:{_bare_digest(digest)[:24]}",
            scheduler_ref=scheduler_ref,
            command=command,
            handler_binding=handler_binding,
            task_before=task_before,
            task_running=attempt_start.task,
            attempt=attempt_start.attempt,
            transition=attempt_start.transition,
            reservation=reservation,
            budget_mutation=budget_mutation,
            launch_commit=launch_commit,
            ticket_digest=digest,
        )


class SchedulerTaskLaunchPreparationService:
    """Applies one admitted decision and stops before handler construction."""

    def apply(
        self,
        *,
        scheduler_ref: str,
        command: CommandT,
        candidate: SchedulerTaskAdmissionCandidate,
        plan: SchedulerTaskAdmissionPlan,
        catalog: SchedulerHandlerCatalog,
        transaction: SchedulerTaskLaunchTransaction,
        applied_at: str,
    ) -> SchedulerHandlerLaunchTicket[CommandT]:
        _require_typed_ref("scheduler_ref", scheduler_ref, "scheduler:")
        _parse_utc("applied_at", applied_at)
        if not isinstance(transaction, SchedulerTaskLaunchTransaction):
            raise SchedulerTaskLaunchPreparationError(
                "transaction doit implémenter SchedulerTaskLaunchTransaction"
            )
        command_ref = getattr(command, "command_ref", None)
        if command_ref != candidate.task.command_ref:
            raise SchedulerTaskLaunchPreparationError(
                "la commande et la tâche candidate ne sont pas corrélées"
            )
        decision = _unique_decision(plan, candidate.task.task_ref)
        if decision.status is not SchedulerAdmissionStatus.ADMITTED:
            raise SchedulerTaskLaunchPreparationError(
                "seule une décision admitted peut être appliquée"
            )
        reservation = decision.reservation
        if reservation is None:
            raise SchedulerTaskLaunchPreparationError(
                "une admission appliquée exige une réservation"
            )
        _validate_application_window(
            plan=plan,
            decision=decision,
            reservation=reservation,
            applied_at=applied_at,
        )
        binding = catalog.resolve_for(
            command,
            capability_ref=candidate.task.capability_ref,
            contract_version=candidate.task.contract_version,
        )
        _validate_binding(candidate, binding)
        budget_mutation = SchedulerCommandBudgetMutation.create(
            budget=candidate.command_budget,
            charge=candidate.budget_charge,
        )
        cause_ref = f"scheduler-admission-plan:{_bare_digest(plan.plan_digest)[:24]}"
        attempt_start = candidate.task.start_attempt(
            handler_ref=binding.handler_ref,
            contract_version=binding.key.contract_version,
            started_at=applied_at,
            deadline_at=decision.attempt_deadline_at,
            actor_ref=scheduler_ref,
            cause_ref=cause_ref,
            effective_priority=decision.effective_priority,
        )
        commit = transaction.commit_launch(
            scheduler_ref=scheduler_ref,
            plan=plan,
            decision=decision,
            task_before=candidate.task,
            attempt_start=attempt_start,
            budget_mutation=budget_mutation,
            reservation=reservation,
            handler_binding=binding,
            committed_at=applied_at,
        )
        _validate_commit(
            commit=commit,
            scheduler_ref=scheduler_ref,
            plan=plan,
            attempt_start=attempt_start,
            reservation=reservation,
            budget_mutation=budget_mutation,
            applied_at=applied_at,
        )
        return SchedulerHandlerLaunchTicket.create(
            scheduler_ref=scheduler_ref,
            command=command,
            handler_binding=binding,
            task_before=candidate.task,
            attempt_start=attempt_start,
            reservation=reservation,
            budget_mutation=budget_mutation,
            launch_commit=commit,
        )


def _unique_decision(
    plan: SchedulerTaskAdmissionPlan,
    task_ref: str,
) -> SchedulerTaskAdmissionDecision:
    matches = tuple(decision for decision in plan.decisions if decision.task_ref == task_ref)
    if len(matches) != 1:
        raise SchedulerTaskLaunchPreparationError(
            "le plan doit contenir exactement une décision pour task_ref"
        )
    return matches[0]


def _validate_application_window(
    *,
    plan: SchedulerTaskAdmissionPlan,
    decision: SchedulerTaskAdmissionDecision,
    reservation: SchedulerResourceReservation,
    applied_at: str,
) -> None:
    applied = _parse_utc("applied_at", applied_at)
    if applied < _parse_utc("planned_at", plan.planned_at):
        raise SchedulerTaskLaunchPreparationError(
            "applied_at ne peut pas précéder le plan d’admission"
        )
    if applied >= _parse_utc("attempt_deadline_at", decision.attempt_deadline_at):
        raise SchedulerTaskLaunchPreparationError(
            "la fenêtre de lancement de la tentative est expirée"
        )
    if applied >= _parse_utc("reservation.expires_at", reservation.expires_at):
        raise SchedulerTaskLaunchPreparationError(
            "la réservation de ressources est expirée"
        )


def _validate_binding(
    candidate: SchedulerTaskAdmissionCandidate,
    binding: SchedulerHandlerBinding,
) -> None:
    policy = binding.descriptor.execution_policy
    if policy.resource_profile_ref != candidate.resource_profile.profile_ref:
        raise SchedulerTaskLaunchPreparationError(
            "le profil de ressources du handler diverge du plan d’admission"
        )
    if policy.retry_policy_ref != candidate.retry_policy.policy_ref:
        raise SchedulerTaskLaunchPreparationError(
            "la politique de reprise du handler diverge du plan d’admission"
        )


def _validate_commit(
    *,
    commit: SchedulerTaskLaunchCommit,
    scheduler_ref: str,
    plan: SchedulerTaskAdmissionPlan,
    attempt_start: SchedulerTaskAttemptStart,
    reservation: SchedulerResourceReservation,
    budget_mutation: SchedulerCommandBudgetMutation,
    applied_at: str,
) -> None:
    expected = (
        (commit.scheduler_ref, scheduler_ref, "scheduler_ref"),
        (commit.command_ref, attempt_start.task.command_ref, "command_ref"),
        (commit.task_ref, attempt_start.task.task_ref, "task_ref"),
        (commit.attempt_ref, attempt_start.attempt.attempt_ref, "attempt_ref"),
        (commit.reservation_ref, reservation.reservation_ref, "reservation_ref"),
        (commit.admission_plan_digest, plan.plan_digest, "admission_plan_digest"),
        (commit.task_state_version, attempt_start.task.state_version, "task_state_version"),
        (
            commit.scheduler_steps_after,
            budget_mutation.scheduler_steps_after,
            "scheduler_steps_after",
        ),
        (
            commit.specialist_visits_after,
            budget_mutation.specialist_visits_after,
            "specialist_visits_after",
        ),
        (commit.committed_at, applied_at, "committed_at"),
    )
    for actual, wanted, name in expected:
        if actual != wanted:
            raise SchedulerTaskLaunchPreparationError(
                f"le receipt transactionnel diverge pour {name}"
            )


def _budget_mutation_digest(
    *,
    budget_ref: str,
    command_ref: str,
    scheduler_steps_before: int,
    scheduler_steps_after: int,
    specialist_visits_before: int,
    specialist_visits_after: int,
    charge: SchedulerBudgetCharge,
) -> str:
    return _length_prefixed_digest(
        (
            ("budget_ref", budget_ref),
            ("command_ref", command_ref),
            ("scheduler_steps_before", scheduler_steps_before),
            ("scheduler_steps_after", scheduler_steps_after),
            ("specialist_visits_before", specialist_visits_before),
            ("specialist_visits_after", specialist_visits_after),
            ("charge.scheduler_steps", charge.scheduler_steps),
            ("charge.specialist_visits", charge.specialist_visits),
        )
    )


def _launch_commit_digest(
    *,
    scheduler_ref: str,
    command_ref: str,
    task_ref: str,
    attempt_ref: str,
    reservation_ref: str,
    admission_plan_digest: str,
    task_state_version: int,
    scheduler_steps_after: int,
    specialist_visits_after: int,
    committed_at: str,
) -> str:
    return _length_prefixed_digest(
        (
            ("scheduler_ref", scheduler_ref),
            ("command_ref", command_ref),
            ("task_ref", task_ref),
            ("attempt_ref", attempt_ref),
            ("reservation_ref", reservation_ref),
            ("admission_plan_digest", admission_plan_digest),
            ("task_state_version", task_state_version),
            ("scheduler_steps_after", scheduler_steps_after),
            ("specialist_visits_after", specialist_visits_after),
            ("committed_at", committed_at),
        )
    )


def _ticket_digest(
    *,
    scheduler_ref: str,
    command_ref: str,
    task_digest: str,
    attempt_ref: str,
    reservation_digest: str,
    budget_mutation_digest: str,
    commit_digest: str,
    handler_ref: str,
) -> str:
    return _length_prefixed_digest(
        (
            ("scheduler_ref", scheduler_ref),
            ("command_ref", command_ref),
            ("task_digest", task_digest),
            ("attempt_ref", attempt_ref),
            ("reservation_digest", reservation_digest),
            ("budget_mutation_digest", budget_mutation_digest),
            ("commit_digest", commit_digest),
            ("handler_ref", handler_ref),
        )
    )


def _length_prefixed_digest(fields: tuple[tuple[str, object], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in fields:
        raw = f"{name}={value}".encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return f"sha256:{digest.hexdigest()}"


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _parse_utc(name: str, value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SchedulerTaskLaunchPreparationError(f"{name} doit être UTC et finir par Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SchedulerTaskLaunchPreparationError(f"{name} est invalide") from exc
    if parsed.tzinfo != timezone.utc:
        raise SchedulerTaskLaunchPreparationError(f"{name} doit être UTC")
    return parsed


def _require_typed_ref(name: str, value: object, prefix: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith(prefix)
        or _TYPED_REF_RE.fullmatch(value) is None
    ):
        raise SchedulerTaskLaunchPreparationError(
            f"{name} doit commencer par {prefix}"
        )


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SchedulerTaskLaunchPreparationError(f"{name} doit être un sha256")


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SchedulerTaskLaunchPreparationError(
            f"{name} doit être un entier strictement positif"
        )


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SchedulerTaskLaunchPreparationError(
            f"{name} doit être un entier positif ou nul"
        )


__all__ = (
    "SCHEDULER_HANDLER_LAUNCH_TICKET_SCHEMA",
    "SCHEDULER_TASK_LAUNCH_COMMIT_SCHEMA",
    "SchedulerCommandBudgetMutation",
    "SchedulerHandlerLaunchTicket",
    "SchedulerTaskLaunchCommit",
    "SchedulerTaskLaunchPreparationError",
    "SchedulerTaskLaunchPreparationService",
    "SchedulerTaskLaunchTransaction",
)
