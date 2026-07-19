from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import math
import re

from kernel.scheduler_task_model import SchedulerTask, SchedulerTaskState


_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SchedulerTaskAdmissionError(ValueError):
    """Erreur de contrat du planificateur pur d'admission Scheduler."""


class SchedulerAdmissionStatus(str, Enum):
    """Décision pure; aucun effet n'est appliqué par ce module."""

    ADMITTED = "admitted"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class SchedulerAdmissionReason(str, Enum):
    """Motifs stables et auditables d'admission, attente ou refus."""

    ADMITTED = "admitted"
    TASK_NOT_READY = "task-not-ready"
    TASK_TERMINAL = "task-terminal"
    ATTEMPT_BUDGET_EXHAUSTED = "attempt-budget-exhausted"
    COMMAND_STEP_BUDGET_EXHAUSTED = "command-step-budget-exhausted"
    SPECIALIST_VISIT_BUDGET_EXHAUSTED = "specialist-visit-budget-exhausted"
    COMMAND_DEADLINE_EXPIRED = "command-deadline-expired"
    RETRY_BACKOFF_ACTIVE = "retry-backoff-active"
    RESOURCE_UNAVAILABLE = "resource-unavailable"
    ADMISSION_WINDOW_FULL = "admission-window-full"


@dataclass(frozen=True, slots=True)
class SchedulerBudgetCharge:
    """Coût borné prévu pour une seule admission de tâche."""

    scheduler_steps: int = 1
    specialist_visits: int = 0

    def __post_init__(self) -> None:
        _require_positive_int("scheduler_steps", self.scheduler_steps)
        _require_non_negative_int("specialist_visits", self.specialist_visits)


@dataclass(frozen=True, slots=True)
class SchedulerCommandExecutionBudget:
    """Budget global durable d'une commande, lu mais non muté ici."""

    budget_ref: str
    command_ref: str
    max_scheduler_steps: int
    consumed_scheduler_steps: int
    max_specialist_visits: int
    consumed_specialist_visits: int
    started_at: str
    deadline_at: str

    def __post_init__(self) -> None:
        _require_typed_ref("budget_ref", self.budget_ref, "scheduler-command-budget:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_positive_int("max_scheduler_steps", self.max_scheduler_steps)
        _require_non_negative_int(
            "consumed_scheduler_steps", self.consumed_scheduler_steps
        )
        _require_non_negative_int("max_specialist_visits", self.max_specialist_visits)
        _require_non_negative_int(
            "consumed_specialist_visits", self.consumed_specialist_visits
        )
        if self.consumed_scheduler_steps > self.max_scheduler_steps:
            raise SchedulerTaskAdmissionError(
                "consumed_scheduler_steps dépasse max_scheduler_steps"
            )
        if self.consumed_specialist_visits > self.max_specialist_visits:
            raise SchedulerTaskAdmissionError(
                "consumed_specialist_visits dépasse max_specialist_visits"
            )
        started = _parse_utc("started_at", self.started_at)
        deadline = _parse_utc("deadline_at", self.deadline_at)
        if deadline <= started:
            raise SchedulerTaskAdmissionError("deadline_at doit suivre started_at")

    def remaining_scheduler_steps(self) -> int:
        return self.max_scheduler_steps - self.consumed_scheduler_steps

    def remaining_specialist_visits(self) -> int:
        return self.max_specialist_visits - self.consumed_specialist_visits

    def deadline_expired(self, now: str) -> bool:
        return _parse_utc("now", now) >= _parse_utc("deadline_at", self.deadline_at)

    def refusal_for(self, charge: SchedulerBudgetCharge) -> SchedulerAdmissionReason | None:
        if charge.scheduler_steps > self.remaining_scheduler_steps():
            return SchedulerAdmissionReason.COMMAND_STEP_BUDGET_EXHAUSTED
        if charge.specialist_visits > self.remaining_specialist_visits():
            return SchedulerAdmissionReason.SPECIALIST_VISIT_BUDGET_EXHAUSTED
        return None


@dataclass(frozen=True, slots=True)
class SchedulerTaskExecutionBudget:
    """Bornes propres à une tâche et à chacune de ses tentatives."""

    budget_ref: str
    task_ref: str
    max_attempts: int
    timeout_seconds: int

    def __post_init__(self) -> None:
        _require_typed_ref("budget_ref", self.budget_ref, "scheduler-task-budget:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_positive_int("max_attempts", self.max_attempts)
        _require_positive_int("timeout_seconds", self.timeout_seconds)

    def attempts_exhausted(self, task: SchedulerTask) -> bool:
        self.validate_task(task)
        return task.attempt_count >= self.max_attempts

    def validate_task(self, task: SchedulerTask) -> None:
        if task.task_ref != self.task_ref:
            raise SchedulerTaskAdmissionError(
                "le budget de tâche ne correspond pas à task_ref"
            )
        if task.max_attempts != self.max_attempts:
            raise SchedulerTaskAdmissionError(
                "max_attempts doit être identique dans la tâche et son budget"
            )

    def attempt_deadline(self, *, now: str, command_deadline_at: str) -> str:
        current = _parse_utc("now", now)
        command_deadline = _parse_utc("command_deadline_at", command_deadline_at)
        timeout_deadline = current + timedelta(seconds=self.timeout_seconds)
        return _format_utc(min(timeout_deadline, command_deadline))


@dataclass(frozen=True, slots=True)
class SchedulerRetryPolicy:
    """Backoff entier, déterministe et borné, décidé par politique."""

    policy_ref: str
    base_delay_seconds: int
    multiplier: int
    max_delay_seconds: int

    def __post_init__(self) -> None:
        _require_typed_ref("policy_ref", self.policy_ref, "retry-policy:")
        _require_non_negative_int("base_delay_seconds", self.base_delay_seconds)
        _require_positive_int("multiplier", self.multiplier)
        _require_non_negative_int("max_delay_seconds", self.max_delay_seconds)
        if self.max_delay_seconds < self.base_delay_seconds:
            raise SchedulerTaskAdmissionError(
                "max_delay_seconds doit être supérieur ou égal à base_delay_seconds"
            )

    def delay_seconds(self, *, failed_attempt_number: int) -> int:
        _require_positive_int("failed_attempt_number", failed_attempt_number)
        if self.base_delay_seconds == 0:
            return 0
        delay = self.base_delay_seconds * (
            self.multiplier ** max(0, failed_attempt_number - 1)
        )
        return min(delay, self.max_delay_seconds)

    def retry_not_before(self, *, failed_at: str, failed_attempt_number: int) -> str:
        failed = _parse_utc("failed_at", failed_at)
        return _format_utc(
            failed + timedelta(seconds=self.delay_seconds(
                failed_attempt_number=failed_attempt_number
            ))
        )


@dataclass(frozen=True, slots=True)
class SchedulerFairnessPolicy:
    """Vieillissement explicite afin d'empêcher la famine des tâches prêtes."""

    policy_ref: str
    aging_interval_seconds: int
    aging_priority_points: int
    maximum_priority: int = 100
    deadline_boost_window_seconds: int = 0
    deadline_boost_points: int = 0

    def __post_init__(self) -> None:
        _require_typed_ref("policy_ref", self.policy_ref, "fairness-policy:")
        _require_positive_int("aging_interval_seconds", self.aging_interval_seconds)
        _require_non_negative_int("aging_priority_points", self.aging_priority_points)
        _require_int_range("maximum_priority", self.maximum_priority, 0, 100)
        _require_non_negative_int(
            "deadline_boost_window_seconds", self.deadline_boost_window_seconds
        )
        _require_non_negative_int("deadline_boost_points", self.deadline_boost_points)

    def effective_priority(
        self,
        *,
        task: SchedulerTask,
        now: str,
        command_deadline_at: str,
    ) -> int:
        current = _parse_utc("now", now)
        created = _parse_utc("task.created_at", task.created_at)
        deadline = _parse_utc("command_deadline_at", command_deadline_at)
        waited_seconds = max(0, int((current - created).total_seconds()))
        aging_periods = waited_seconds // self.aging_interval_seconds
        priority = task.initial_priority + aging_periods * self.aging_priority_points
        remaining_seconds = int((deadline - current).total_seconds())
        if (
            self.deadline_boost_window_seconds > 0
            and 0 <= remaining_seconds <= self.deadline_boost_window_seconds
        ):
            priority += self.deadline_boost_points
        return min(self.maximum_priority, max(0, priority))


@dataclass(frozen=True, slots=True)
class SchedulerResourceRequirement:
    """Quantité atomique requise par un profil de handler."""

    resource_ref: str
    amount: int
    exclusive: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("resource_ref", self.resource_ref, "resource:")
        _require_positive_int("amount", self.amount)
        if not isinstance(self.exclusive, bool):
            raise SchedulerTaskAdmissionError("exclusive doit être booléen")
        if self.exclusive and self.amount != 1:
            raise SchedulerTaskAdmissionError(
                "une ressource exclusive doit être demandée avec amount=1"
            )


@dataclass(frozen=True, slots=True)
class SchedulerResourceProfile:
    """Profil résolu depuis le descripteur du handler, sans registre implicite."""

    profile_ref: str
    requirements: tuple[SchedulerResourceRequirement, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("profile_ref", self.profile_ref, "resource-profile:")
        requirements = tuple(self.requirements)
        if len({item.resource_ref for item in requirements}) != len(requirements):
            raise SchedulerTaskAdmissionError(
                "requirements contient une ressource dupliquée"
            )
        object.__setattr__(self, "requirements", requirements)


@dataclass(frozen=True, slots=True)
class SchedulerResourceInventoryItem:
    """Photographie légère de capacité; l'autorité durable reste hors de ce module."""

    resource_ref: str
    capacity: int
    reserved: int

    def __post_init__(self) -> None:
        _require_typed_ref("resource_ref", self.resource_ref, "resource:")
        _require_non_negative_int("capacity", self.capacity)
        _require_non_negative_int("reserved", self.reserved)
        if self.reserved > self.capacity:
            raise SchedulerTaskAdmissionError("reserved dépasse capacity")

    @property
    def available(self) -> int:
        return self.capacity - self.reserved


@dataclass(frozen=True, slots=True)
class SchedulerResourceReservation:
    """Réservation proposée par le plan; aucun port réel n'est appelé ici."""

    reservation_ref: str
    task_ref: str
    profile_ref: str
    requirements: tuple[SchedulerResourceRequirement, ...]
    reserved_at: str
    expires_at: str
    reservation_digest: str

    def __post_init__(self) -> None:
        _require_typed_ref(
            "reservation_ref", self.reservation_ref, "scheduler-reservation:"
        )
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("profile_ref", self.profile_ref, "resource-profile:")
        _parse_utc("reserved_at", self.reserved_at)
        if _parse_utc("expires_at", self.expires_at) <= _parse_utc(
            "reserved_at", self.reserved_at
        ):
            raise SchedulerTaskAdmissionError("expires_at doit suivre reserved_at")
        requirements = tuple(self.requirements)
        object.__setattr__(self, "requirements", requirements)
        _require_sha256("reservation_digest", self.reservation_digest)
        expected = _reservation_digest(
            task_ref=self.task_ref,
            profile_ref=self.profile_ref,
            requirements=requirements,
            reserved_at=self.reserved_at,
            expires_at=self.expires_at,
        )
        if self.reservation_digest != expected:
            raise SchedulerTaskAdmissionError("reservation_digest incohérent")
        if self.reservation_ref != (
            f"scheduler-reservation:{_bare_digest(expected)[:24]}"
        ):
            raise SchedulerTaskAdmissionError("reservation_ref incohérent")

    @classmethod
    def create(
        cls,
        *,
        task_ref: str,
        profile: SchedulerResourceProfile,
        reserved_at: str,
        expires_at: str,
    ) -> SchedulerResourceReservation:
        digest = _reservation_digest(
            task_ref=task_ref,
            profile_ref=profile.profile_ref,
            requirements=profile.requirements,
            reserved_at=reserved_at,
            expires_at=expires_at,
        )
        return cls(
            reservation_ref=f"scheduler-reservation:{_bare_digest(digest)[:24]}",
            task_ref=task_ref,
            profile_ref=profile.profile_ref,
            requirements=profile.requirements,
            reserved_at=reserved_at,
            expires_at=expires_at,
            reservation_digest=digest,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskAdmissionCandidate:
    """Toutes les données résolues nécessaires à une décision pure."""

    task: SchedulerTask
    command_budget: SchedulerCommandExecutionBudget
    task_budget: SchedulerTaskExecutionBudget
    budget_charge: SchedulerBudgetCharge
    resource_profile: SchedulerResourceProfile
    fairness_policy: SchedulerFairnessPolicy
    retry_policy: SchedulerRetryPolicy
    retry_not_before: str = ""

    def __post_init__(self) -> None:
        if self.task.command_ref != self.command_budget.command_ref:
            raise SchedulerTaskAdmissionError(
                "la tâche et le budget de commande ne sont pas corrélés"
            )
        self.task_budget.validate_task(self.task)
        if self.retry_not_before:
            _parse_utc("retry_not_before", self.retry_not_before)

    def effective_priority(self, *, now: str) -> int:
        return self.fairness_policy.effective_priority(
            task=self.task,
            now=now,
            command_deadline_at=self.command_budget.deadline_at,
        )


@dataclass(frozen=True, slots=True)
class SchedulerTaskAdmissionDecision:
    """Décision auditable produite pour une tâche candidate."""

    task_ref: str
    status: SchedulerAdmissionStatus
    reason: SchedulerAdmissionReason
    effective_priority: int
    attempt_deadline_at: str
    retry_not_before: str
    reservation: SchedulerResourceReservation | None

    def __post_init__(self) -> None:
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_int_range("effective_priority", self.effective_priority, 0, 100)
        if self.status is SchedulerAdmissionStatus.ADMITTED:
            if self.reason is not SchedulerAdmissionReason.ADMITTED:
                raise SchedulerTaskAdmissionError(
                    "une admission doit porter reason=admitted"
                )
            if self.reservation is None or not self.attempt_deadline_at:
                raise SchedulerTaskAdmissionError(
                    "une admission exige réservation et échéance de tentative"
                )
            _parse_utc("attempt_deadline_at", self.attempt_deadline_at)
        else:
            if self.reservation is not None or self.attempt_deadline_at:
                raise SchedulerTaskAdmissionError(
                    "une tâche non admise ne réserve aucune ressource"
                )
        if self.retry_not_before:
            _parse_utc("retry_not_before", self.retry_not_before)


@dataclass(frozen=True, slots=True)
class SchedulerTaskAdmissionPlan:
    """Plan immuable; son application appartiendra au Scheduler vivant."""

    planned_at: str
    max_admissions: int
    decisions: tuple[SchedulerTaskAdmissionDecision, ...]
    plan_digest: str

    def __post_init__(self) -> None:
        _parse_utc("planned_at", self.planned_at)
        _require_positive_int("max_admissions", self.max_admissions)
        decisions = tuple(self.decisions)
        if len({decision.task_ref for decision in decisions}) != len(decisions):
            raise SchedulerTaskAdmissionError("decisions contient une tâche dupliquée")
        object.__setattr__(self, "decisions", decisions)
        if sum(
            decision.status is SchedulerAdmissionStatus.ADMITTED
            for decision in decisions
        ) > self.max_admissions:
            raise SchedulerTaskAdmissionError("le plan dépasse max_admissions")
        _require_sha256("plan_digest", self.plan_digest)
        expected = _admission_plan_digest(
            planned_at=self.planned_at,
            max_admissions=self.max_admissions,
            decisions=self.decisions,
        )
        if self.plan_digest != expected:
            raise SchedulerTaskAdmissionError("plan_digest incohérent")

    @classmethod
    def create(
        cls,
        *,
        planned_at: str,
        max_admissions: int,
        decisions: Sequence[SchedulerTaskAdmissionDecision],
    ) -> SchedulerTaskAdmissionPlan:
        values = tuple(decisions)
        return cls(
            planned_at=planned_at,
            max_admissions=max_admissions,
            decisions=values,
            plan_digest=_admission_plan_digest(
                planned_at=planned_at,
                max_admissions=max_admissions,
                decisions=values,
            ),
        )


class SchedulerTaskAdmissionPlanner:
    """Planifie sans muter tâches, budgets, SQL, ressources ou handlers."""

    def plan(
        self,
        *,
        candidates: Iterable[SchedulerTaskAdmissionCandidate],
        inventory: Iterable[SchedulerResourceInventoryItem],
        now: str,
        max_admissions: int,
    ) -> SchedulerTaskAdmissionPlan:
        _parse_utc("now", now)
        _require_positive_int("max_admissions", max_admissions)
        candidate_values = tuple(candidates)
        if len({item.task.task_ref for item in candidate_values}) != len(
            candidate_values
        ):
            raise SchedulerTaskAdmissionError("candidates contient une tâche dupliquée")
        inventory_values = tuple(inventory)
        inventory_by_ref = _inventory_mapping(inventory_values)
        available = {
            resource_ref: item.available
            for resource_ref, item in inventory_by_ref.items()
        }
        ordered = tuple(
            sorted(
                candidate_values,
                key=lambda item: (
                    -item.effective_priority(now=now),
                    item.command_budget.deadline_at,
                    item.task.created_at,
                    item.task.task_ref,
                ),
            )
        )
        decisions: list[SchedulerTaskAdmissionDecision] = []
        admitted_count = 0
        for candidate in ordered:
            priority = candidate.effective_priority(now=now)
            decision = self._decide_before_resources(
                candidate=candidate,
                now=now,
                effective_priority=priority,
            )
            if decision is not None:
                decisions.append(decision)
                continue
            if admitted_count >= max_admissions:
                decisions.append(
                    _decision(
                        candidate,
                        status=SchedulerAdmissionStatus.DEFERRED,
                        reason=SchedulerAdmissionReason.ADMISSION_WINDOW_FULL,
                        effective_priority=priority,
                    )
                )
                continue
            if not _resources_available(candidate.resource_profile, available):
                decisions.append(
                    _decision(
                        candidate,
                        status=SchedulerAdmissionStatus.DEFERRED,
                        reason=SchedulerAdmissionReason.RESOURCE_UNAVAILABLE,
                        effective_priority=priority,
                    )
                )
                continue
            deadline = candidate.task_budget.attempt_deadline(
                now=now,
                command_deadline_at=candidate.command_budget.deadline_at,
            )
            reservation = SchedulerResourceReservation.create(
                task_ref=candidate.task.task_ref,
                profile=candidate.resource_profile,
                reserved_at=now,
                expires_at=deadline,
            )
            _reserve(candidate.resource_profile, available)
            admitted_count += 1
            decisions.append(
                SchedulerTaskAdmissionDecision(
                    task_ref=candidate.task.task_ref,
                    status=SchedulerAdmissionStatus.ADMITTED,
                    reason=SchedulerAdmissionReason.ADMITTED,
                    effective_priority=priority,
                    attempt_deadline_at=deadline,
                    retry_not_before=candidate.retry_not_before,
                    reservation=reservation,
                )
            )
        return SchedulerTaskAdmissionPlan.create(
            planned_at=now,
            max_admissions=max_admissions,
            decisions=decisions,
        )

    @staticmethod
    def _decide_before_resources(
        *,
        candidate: SchedulerTaskAdmissionCandidate,
        now: str,
        effective_priority: int,
    ) -> SchedulerTaskAdmissionDecision | None:
        task = candidate.task
        if task.state.terminal:
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.REJECTED,
                reason=SchedulerAdmissionReason.TASK_TERMINAL,
                effective_priority=effective_priority,
            )
        if task.state is not SchedulerTaskState.READY:
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.DEFERRED,
                reason=SchedulerAdmissionReason.TASK_NOT_READY,
                effective_priority=effective_priority,
            )
        if candidate.task_budget.attempts_exhausted(task):
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.REJECTED,
                reason=SchedulerAdmissionReason.ATTEMPT_BUDGET_EXHAUSTED,
                effective_priority=effective_priority,
            )
        if candidate.command_budget.deadline_expired(now):
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.REJECTED,
                reason=SchedulerAdmissionReason.COMMAND_DEADLINE_EXPIRED,
                effective_priority=effective_priority,
            )
        budget_refusal = candidate.command_budget.refusal_for(candidate.budget_charge)
        if budget_refusal is not None:
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.REJECTED,
                reason=budget_refusal,
                effective_priority=effective_priority,
            )
        if candidate.retry_not_before and _parse_utc(
            "retry_not_before", candidate.retry_not_before
        ) > _parse_utc("now", now):
            return _decision(
                candidate,
                status=SchedulerAdmissionStatus.DEFERRED,
                reason=SchedulerAdmissionReason.RETRY_BACKOFF_ACTIVE,
                effective_priority=effective_priority,
            )
        return None


def _decision(
    candidate: SchedulerTaskAdmissionCandidate,
    *,
    status: SchedulerAdmissionStatus,
    reason: SchedulerAdmissionReason,
    effective_priority: int,
) -> SchedulerTaskAdmissionDecision:
    return SchedulerTaskAdmissionDecision(
        task_ref=candidate.task.task_ref,
        status=status,
        reason=reason,
        effective_priority=effective_priority,
        attempt_deadline_at="",
        retry_not_before=candidate.retry_not_before,
        reservation=None,
    )


def _inventory_mapping(
    items: Sequence[SchedulerResourceInventoryItem],
) -> Mapping[str, SchedulerResourceInventoryItem]:
    result: dict[str, SchedulerResourceInventoryItem] = {}
    for item in items:
        if item.resource_ref in result:
            raise SchedulerTaskAdmissionError(
                "inventory contient une ressource dupliquée"
            )
        result[item.resource_ref] = item
    return result


def _resources_available(
    profile: SchedulerResourceProfile,
    available: Mapping[str, int],
) -> bool:
    for requirement in profile.requirements:
        if available.get(requirement.resource_ref, 0) < requirement.amount:
            return False
    return True


def _reserve(profile: SchedulerResourceProfile, available: dict[str, int]) -> None:
    for requirement in profile.requirements:
        available[requirement.resource_ref] -= requirement.amount


def _reservation_digest(
    *,
    task_ref: str,
    profile_ref: str,
    requirements: Sequence[SchedulerResourceRequirement],
    reserved_at: str,
    expires_at: str,
) -> str:
    parts: list[tuple[str, object]] = [
        ("task_ref", task_ref),
        ("profile_ref", profile_ref),
        ("reserved_at", reserved_at),
        ("expires_at", expires_at),
    ]
    for item in requirements:
        parts.extend(
            (
                ("resource_ref", item.resource_ref),
                ("amount", item.amount),
                ("exclusive", item.exclusive),
            )
        )
    return "sha256:" + _length_prefixed_digest(parts)


def _admission_plan_digest(
    *,
    planned_at: str,
    max_admissions: int,
    decisions: Sequence[SchedulerTaskAdmissionDecision],
) -> str:
    parts: list[tuple[str, object]] = [
        ("planned_at", planned_at),
        ("max_admissions", max_admissions),
    ]
    for decision in decisions:
        parts.extend(
            (
                ("task_ref", decision.task_ref),
                ("status", decision.status.value),
                ("reason", decision.reason.value),
                ("effective_priority", decision.effective_priority),
                ("attempt_deadline_at", decision.attempt_deadline_at),
                ("retry_not_before", decision.retry_not_before),
                (
                    "reservation_ref",
                    decision.reservation.reservation_ref
                    if decision.reservation is not None
                    else "",
                ),
            )
        )
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
            raise SchedulerTaskAdmissionError("les flottants de digest doivent être finis")
        return value.hex()
    if isinstance(value, (str, int)):
        return str(value)
    raise SchedulerTaskAdmissionError(
        f"type scalaire non pris en charge: {type(value).__name__}"
    )


def _parse_utc(name: str, value: object) -> datetime:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise SchedulerTaskAdmissionError(
            f"{name} doit être un horodatage UTC finissant par Z"
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SchedulerTaskAdmissionError(f"{name} est invalide") from exc
    return parsed.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise SchedulerTaskAdmissionError(f"{name} doit être une référence typée")
    if prefix and not value.startswith(prefix):
        raise SchedulerTaskAdmissionError(f"{name} doit commencer par {prefix}")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise SchedulerTaskAdmissionError(f"{name} doit être un SHA-256 préfixé")


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


def _require_positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SchedulerTaskAdmissionError(
            f"{name} doit être un entier strictement positif"
        )


def _require_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SchedulerTaskAdmissionError(
            f"{name} doit être un entier positif ou nul"
        )


def _require_int_range(name: str, value: object, minimum: int, maximum: int) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise SchedulerTaskAdmissionError(
            f"{name} doit être compris entre {minimum} et {maximum}"
        )


__all__ = (
    "SchedulerAdmissionReason",
    "SchedulerAdmissionStatus",
    "SchedulerBudgetCharge",
    "SchedulerCommandExecutionBudget",
    "SchedulerFairnessPolicy",
    "SchedulerResourceInventoryItem",
    "SchedulerResourceProfile",
    "SchedulerResourceRequirement",
    "SchedulerResourceReservation",
    "SchedulerRetryPolicy",
    "SchedulerTaskAdmissionCandidate",
    "SchedulerTaskAdmissionDecision",
    "SchedulerTaskAdmissionError",
    "SchedulerTaskAdmissionPlan",
    "SchedulerTaskAdmissionPlanner",
    "SchedulerTaskExecutionBudget",
)
