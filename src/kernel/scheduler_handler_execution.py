"""Exécution contrôlée d'une capacité de handler sous autorité du Scheduler.

Cette frontière consomme un ``SchedulerHandlerExecutionLease`` déjà armé. Elle
appelle exactement une fois la capacité ``handler.execute()``, borne son temps,
convertit sa fin en objets ``SchedulerTask`` typés, publie au mieux les notices
informatives de fin et tente systématiquement la fermeture de l'instance.

Elle ne persiste rien, ne libère aucune réservation durable, ne choisit aucune
tâche suivante et n'appelle ni Dispatcher, ni EventBus, ni laboratoire par une
voie parallèle. La persistance transactionnelle de l'issue appartient à
l'unité suivante.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import re
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from .scheduler_handler_contract import (
    HandlerInformationSink,
    HandlerLifecycleNotice,
    HandlerLifecyclePhase,
    SchedulerHandler,
)
from .scheduler_handler_instance_lifecycle import (
    HandlerNoticePublication,
    SchedulerHandlerExecutionLease,
)
from .scheduler_task_model import (
    SchedulerTaskAttemptCompletion,
    SchedulerTaskAttemptFailureOutcome,
    SchedulerTaskAttemptInterruption,
    SchedulerTaskFailure,
    SchedulerTaskResult,
    SchedulerTaskState,
)


CommandT = TypeVar("CommandT")
ResultT = TypeVar("ResultT")

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

SCHEDULER_HANDLER_EXECUTION_OUTCOME_SCHEMA = (
    "missipy.scheduler.handler_execution_outcome.v1"
)


class SchedulerHandlerExecutionError(RuntimeError):
    """Erreur de contrat de la frontière d'exécution contrôlée."""


class SchedulerHandlerExecutionStatus(str, Enum):
    """Issue typée rendue au Scheduler après une tentative."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRY_WAIT = "retry-wait"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"


@dataclass(frozen=True, slots=True)
class SchedulerHandlerResultProjection:
    """Métadonnées autorisées pour construire un ``SchedulerTaskResult``."""

    result_type_ref: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("result_type_ref", self.result_type_ref, "result-type:")
        refs = _validated_refs("evidence_refs", self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)


@runtime_checkable
class SchedulerHandlerResultProjector(Protocol[ResultT]):
    """Projection explicite du résultat métier vers le contrat Scheduler."""

    def project(
        self,
        *,
        result: ResultT,
        lease: SchedulerHandlerExecutionLease[Any],
    ) -> SchedulerHandlerResultProjection: ...


@dataclass(frozen=True, slots=True)
class SchedulerHandlerFailureClassification:
    """Classification injectée; l'exécuteur n'invente pas une politique de retry."""

    error_type: str
    message: str
    retryable: bool
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty("error_type", self.error_type)
        _require_non_empty("message", self.message)
        if not isinstance(self.retryable, bool):
            raise TypeError("retryable doit être booléen")
        refs = _validated_refs("evidence_refs", self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)


@runtime_checkable
class SchedulerHandlerFailureClassifier(Protocol):
    """Port de classification fourni par la politique du Scheduler."""

    def classify(
        self,
        *,
        error: BaseException,
        lease: SchedulerHandlerExecutionLease[Any],
    ) -> SchedulerHandlerFailureClassification: ...


@runtime_checkable
class SchedulerCancellationSignal(Protocol):
    """Signal coopératif injecté par le Scheduler, sans file ou bus parallèle."""

    def is_cancelled(self) -> bool: ...

    async def wait(self) -> None: ...


@runtime_checkable
class SchedulerHandlerCloser(Protocol):
    """Fermeture explicitement injectée pour une instance de handler."""

    async def close(
        self,
        *,
        handler: SchedulerHandler[Any, Any],
        lease: SchedulerHandlerExecutionLease[Any],
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class SchedulerHandlerCloseReceipt:
    """Trace de la tentative de fermeture réelle de l'instance."""

    attempted: bool
    closed: bool
    error_type: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        if not self.attempted:
            raise TypeError("la fermeture doit toujours être tentée")
        if self.closed and (self.error_type or self.error_message):
            raise TypeError("une fermeture réussie ne porte pas d'erreur")
        if not self.closed and not self.error_type:
            raise TypeError("une fermeture échouée exige error_type")


@dataclass(frozen=True, slots=True)
class SchedulerHandlerExecutionOutcome(Generic[ResultT]):
    """Issue complète en mémoire, prête pour la transaction durable suivante."""

    schema: str
    outcome_ref: str
    status: SchedulerHandlerExecutionStatus
    lease: SchedulerHandlerExecutionLease[Any] = field(repr=False, compare=False)
    finished_notice: HandlerLifecycleNotice = field(repr=False)
    finished_publication: HandlerNoticePublication = field(repr=False)
    closed_notice: HandlerLifecycleNotice = field(repr=False)
    closed_publication: HandlerNoticePublication = field(repr=False)
    close_receipt: SchedulerHandlerCloseReceipt
    finished_at: str
    elapsed_ms: int
    outcome_digest: str
    handler_result: ResultT | None = field(default=None, repr=False, compare=False)
    completion: SchedulerTaskAttemptCompletion | None = None
    failure_outcome: SchedulerTaskAttemptFailureOutcome | None = None
    interruption: SchedulerTaskAttemptInterruption | None = None

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_HANDLER_EXECUTION_OUTCOME_SCHEMA:
            raise SchedulerHandlerExecutionError(
                "unsupported Scheduler handler execution outcome schema"
            )
        _require_typed_ref("outcome_ref", self.outcome_ref, "handler-outcome:")
        _parse_utc("finished_at", self.finished_at)
        if isinstance(self.elapsed_ms, bool) or not isinstance(self.elapsed_ms, int):
            raise TypeError("elapsed_ms doit être un entier")
        if self.elapsed_ms < 0:
            raise TypeError("elapsed_ms doit être positif ou nul")
        if self.finished_publication.notice is not self.finished_notice:
            raise SchedulerHandlerExecutionError(
                "finished_publication doit référencer finished_notice"
            )
        if self.closed_publication.notice is not self.closed_notice:
            raise SchedulerHandlerExecutionError(
                "closed_publication doit référencer closed_notice"
            )
        if self.closed_notice.phase is not HandlerLifecyclePhase.CLOSED:
            raise SchedulerHandlerExecutionError("closed_notice doit être CLOSED")
        self._validate_variant()
        _require_sha256("outcome_digest", self.outcome_digest)
        expected = _outcome_digest(
            execution_ref=self.lease.execution_ref,
            status=self.status,
            terminal_ref=self.terminal_ref,
            finished_at=self.finished_at,
            elapsed_ms=self.elapsed_ms,
            close_succeeded=self.close_receipt.closed,
        )
        if self.outcome_digest != expected:
            raise SchedulerHandlerExecutionError("outcome_digest incohérent")
        if self.outcome_ref != f"handler-outcome:{_bare_digest(expected)[:24]}":
            raise SchedulerHandlerExecutionError("outcome_ref incohérent")

    @property
    def terminal_ref(self) -> str:
        if self.completion is not None:
            return self.completion.result.result_ref
        if self.failure_outcome is not None:
            return self.failure_outcome.failure.failure_ref
        if self.interruption is not None:
            return self.interruption.transition.transition_ref
        raise SchedulerHandlerExecutionError("issue sans référence terminale")

    @property
    def task_state(self) -> SchedulerTaskState:
        if self.completion is not None:
            return self.completion.task.state
        if self.failure_outcome is not None:
            return self.failure_outcome.task.state
        if self.interruption is not None:
            return self.interruption.task.state
        raise SchedulerHandlerExecutionError("issue sans état de tâche")

    def _validate_variant(self) -> None:
        variants = sum(
            value is not None
            for value in (self.completion, self.failure_outcome, self.interruption)
        )
        if variants != 1:
            raise SchedulerHandlerExecutionError(
                "une issue exige exactement un bundle terminal"
            )
        if self.status is SchedulerHandlerExecutionStatus.SUCCEEDED:
            if self.completion is None or self.handler_result is None:
                raise SchedulerHandlerExecutionError(
                    "une réussite exige résultat métier et completion"
                )
            if self.finished_notice.phase is not HandlerLifecyclePhase.SUCCEEDED:
                raise SchedulerHandlerExecutionError(
                    "une réussite exige une notice SUCCEEDED"
                )
            return
        if self.handler_result is not None or self.completion is not None:
            raise SchedulerHandlerExecutionError(
                "seule une réussite porte un résultat métier"
            )
        if self.status in {
            SchedulerHandlerExecutionStatus.FAILED,
            SchedulerHandlerExecutionStatus.RETRY_WAIT,
        }:
            if self.failure_outcome is None:
                raise SchedulerHandlerExecutionError(
                    "un échec exige SchedulerTaskAttemptFailureOutcome"
                )
            if self.finished_notice.phase is not HandlerLifecyclePhase.FAILED:
                raise SchedulerHandlerExecutionError(
                    "un échec exige une notice FAILED"
                )
            expected = (
                SchedulerTaskState.RETRY_WAIT
                if self.status is SchedulerHandlerExecutionStatus.RETRY_WAIT
                else SchedulerTaskState.FAILED
            )
            if self.failure_outcome.task.state is not expected:
                raise SchedulerHandlerExecutionError(
                    "l'état de tâche diverge de l'issue d'échec"
                )
            return
        if self.interruption is None:
            raise SchedulerHandlerExecutionError(
                "annulation ou expiration exige une interruption"
            )
        if self.status is SchedulerHandlerExecutionStatus.CANCELLED:
            if self.interruption.task.state is not SchedulerTaskState.CANCELLED:
                raise SchedulerHandlerExecutionError("interruption non cancelled")
            if self.finished_notice.phase is not HandlerLifecyclePhase.CANCELLED:
                raise SchedulerHandlerExecutionError(
                    "une annulation exige une notice CANCELLED"
                )
            return
        if self.status is SchedulerHandlerExecutionStatus.TIMED_OUT:
            if self.interruption.task.state is not SchedulerTaskState.TIMED_OUT:
                raise SchedulerHandlerExecutionError("interruption non timed-out")
            if self.finished_notice.phase is not HandlerLifecyclePhase.FAILED:
                raise SchedulerHandlerExecutionError(
                    "une expiration exige une notice FAILED"
                )
            return
        raise SchedulerHandlerExecutionError("status non pris en charge")


class SchedulerHandlerExecutionService:
    """Exécute une capacité bornée et rend une issue typée au Scheduler."""

    async def execute(
        self,
        *,
        lease: SchedulerHandlerExecutionLease[CommandT],
        result_projector: SchedulerHandlerResultProjector[Any],
        failure_classifier: SchedulerHandlerFailureClassifier,
        closer: SchedulerHandlerCloser,
        information_sink: HandlerInformationSink,
        utc_now: Callable[[], str],
        cancellation_signal: SchedulerCancellationSignal | None = None,
    ) -> SchedulerHandlerExecutionOutcome[Any]:
        _validate_lease(lease)
        if not isinstance(result_projector, SchedulerHandlerResultProjector):
            raise TypeError("result_projector doit implémenter le port attendu")
        if not isinstance(failure_classifier, SchedulerHandlerFailureClassifier):
            raise TypeError("failure_classifier doit implémenter le port attendu")
        if not isinstance(closer, SchedulerHandlerCloser):
            raise TypeError("closer doit implémenter le port attendu")
        if cancellation_signal is not None and not isinstance(
            cancellation_signal, SchedulerCancellationSignal
        ):
            raise TypeError("cancellation_signal doit implémenter le port attendu")

        first_now = _parse_utc("utc_now", utc_now())
        deadline = _parse_utc("deadline_at", lease.context.deadline_at)
        remaining = max(0.0, (deadline - first_now).total_seconds())
        descriptor = lease.created.ticket.handler_binding.descriptor
        handler = lease.created.handler
        command = lease.created.ticket.command
        result: Any | None = None
        primary_kind = ""
        primary_error: BaseException | None = None

        handler_task: asyncio.Task[Any] | None = None
        cancellation_task: asyncio.Task[None] | None = None
        try:
            if remaining <= 0:
                primary_kind = "timed-out"
            elif cancellation_signal is not None and cancellation_signal.is_cancelled():
                primary_kind = "cancelled"
            else:
                handler_task = asyncio.create_task(
                    handler.execute(command, lease.context),
                    name=f"handler:{descriptor.handler_ref}",
                )
                waiters: set[asyncio.Task[Any]] = {handler_task}
                if cancellation_signal is not None:
                    cancellation_task = asyncio.create_task(
                        cancellation_signal.wait(),
                        name=f"handler-cancel:{lease.context.attempt_ref}",
                    )
                    waiters.add(cancellation_task)
                done, _pending = await asyncio.wait(
                    waiters,
                    timeout=remaining,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if cancellation_task is not None and cancellation_task in done:
                    primary_kind = "cancelled"
                    await _cancel_task(handler_task)
                elif handler_task in done:
                    try:
                        result = handler_task.result()
                    except asyncio.CancelledError:
                        primary_kind = "cancelled"
                    except Exception as exc:  # la classification est explicite ensuite
                        primary_kind = "failed"
                        primary_error = exc
                    else:
                        primary_kind = "succeeded"
                else:
                    primary_kind = "timed-out"
                    await _cancel_task(handler_task)
        except asyncio.CancelledError:
            primary_kind = "cancelled"
            if handler_task is not None:
                await _cancel_task(handler_task)
        finally:
            if cancellation_task is not None:
                await _cancel_task(cancellation_task)

        finished_at = utc_now()
        finished = _parse_utc("finished_at", finished_at)
        if primary_kind == "succeeded" and finished >= deadline:
            primary_kind = "timed-out"
            result = None
        elapsed_ms = max(
            0,
            int(
                (
                    finished
                    - _parse_utc("started_at", lease.context.started_at)
                ).total_seconds()
                * 1000
            ),
        )

        variant = self._build_variant(
            lease=lease,
            primary_kind=primary_kind,
            primary_error=primary_error,
            result=result,
            result_projector=result_projector,
            failure_classifier=failure_classifier,
            finished_at=finished_at,
        )
        finished_notice = descriptor.notice(
            variant["notice_phase"],
            attributes={
                **_notice_attributes(lease),
                "result_ref": variant["terminal_ref"],
                "elapsed_ms": elapsed_ms,
                "error_type": variant["error_type"],
                "error_message": variant["error_message"],
            },
        )
        finished_publication = _publish_best_effort(
            information_sink, finished_notice
        )
        close_receipt = await _close_best_effort(closer, handler, lease)
        closed_notice = descriptor.notice(
            HandlerLifecyclePhase.CLOSED,
            attributes={
                **_notice_attributes(lease),
                "elapsed_ms": elapsed_ms,
                "error_type": close_receipt.error_type,
                "error_message": close_receipt.error_message,
            },
        )
        closed_publication = _publish_best_effort(information_sink, closed_notice)
        status = variant["status"]
        digest = _outcome_digest(
            execution_ref=lease.execution_ref,
            status=status,
            terminal_ref=variant["terminal_ref"],
            finished_at=finished_at,
            elapsed_ms=elapsed_ms,
            close_succeeded=close_receipt.closed,
        )
        return SchedulerHandlerExecutionOutcome(
            schema=SCHEDULER_HANDLER_EXECUTION_OUTCOME_SCHEMA,
            outcome_ref=f"handler-outcome:{_bare_digest(digest)[:24]}",
            status=status,
            lease=lease,
            handler_result=variant["handler_result"],
            completion=variant["completion"],
            failure_outcome=variant["failure_outcome"],
            interruption=variant["interruption"],
            finished_notice=finished_notice,
            finished_publication=finished_publication,
            closed_notice=closed_notice,
            closed_publication=closed_publication,
            close_receipt=close_receipt,
            finished_at=finished_at,
            elapsed_ms=elapsed_ms,
            outcome_digest=digest,
        )

    def _build_variant(
        self,
        *,
        lease: SchedulerHandlerExecutionLease[Any],
        primary_kind: str,
        primary_error: BaseException | None,
        result: Any | None,
        result_projector: SchedulerHandlerResultProjector[Any],
        failure_classifier: SchedulerHandlerFailureClassifier,
        finished_at: str,
    ) -> dict[str, Any]:
        task = lease.created.ticket.task_running
        attempt = lease.created.ticket.attempt
        cause_ref = lease.execution_ref
        actor_ref = lease.context.scheduler_ref
        if primary_kind == "succeeded":
            try:
                expected_type = lease.created.ticket.handler_binding.descriptor.result_type
                if not isinstance(result, expected_type):
                    raise TypeError(
                        "le résultat du handler diverge de RESULT_TYPE"
                    )
                projection = result_projector.project(result=result, lease=lease)
                scheduler_result = SchedulerTaskResult.create(
                    task_ref=task.task_ref,
                    attempt_ref=attempt.attempt_ref,
                    result_type_ref=projection.result_type_ref,
                    completed_at=finished_at,
                    evidence_refs=projection.evidence_refs,
                )
                completion = task.complete_attempt(
                    attempt=attempt,
                    result=scheduler_result,
                    occurred_at=finished_at,
                    actor_ref=actor_ref,
                    cause_ref=cause_ref,
                )
            except Exception as exc:
                return self._failure_variant(
                    lease=lease,
                    error=exc,
                    classifier=failure_classifier,
                    finished_at=finished_at,
                )
            return {
                "status": SchedulerHandlerExecutionStatus.SUCCEEDED,
                "handler_result": result,
                "completion": completion,
                "failure_outcome": None,
                "interruption": None,
                "notice_phase": HandlerLifecyclePhase.SUCCEEDED,
                "terminal_ref": scheduler_result.result_ref,
                "error_type": "",
                "error_message": "",
            }
        if primary_kind == "cancelled":
            interruption = task.cancel_attempt(
                attempt=attempt,
                occurred_at=finished_at,
                actor_ref=actor_ref,
                cause_ref=cause_ref,
            )
            return {
                "status": SchedulerHandlerExecutionStatus.CANCELLED,
                "handler_result": None,
                "completion": None,
                "failure_outcome": None,
                "interruption": interruption,
                "notice_phase": HandlerLifecyclePhase.CANCELLED,
                "terminal_ref": interruption.transition.transition_ref,
                "error_type": "CancelledError",
                "error_message": "annulation demandée par le Scheduler",
            }
        if primary_kind == "timed-out":
            interruption = task.timeout_attempt(
                attempt=attempt,
                occurred_at=finished_at,
                actor_ref=actor_ref,
                cause_ref=cause_ref,
            )
            return {
                "status": SchedulerHandlerExecutionStatus.TIMED_OUT,
                "handler_result": None,
                "completion": None,
                "failure_outcome": None,
                "interruption": interruption,
                "notice_phase": HandlerLifecyclePhase.FAILED,
                "terminal_ref": interruption.transition.transition_ref,
                "error_type": "TimeoutError",
                "error_message": "deadline de tentative dépassée",
            }
        return self._failure_variant(
            lease=lease,
            error=primary_error or RuntimeError("échec de handler sans exception"),
            classifier=failure_classifier,
            finished_at=finished_at,
        )

    def _failure_variant(
        self,
        *,
        lease: SchedulerHandlerExecutionLease[Any],
        error: BaseException,
        classifier: SchedulerHandlerFailureClassifier,
        finished_at: str,
    ) -> dict[str, Any]:
        classification = _classify_best_effort(classifier, error, lease)
        task = lease.created.ticket.task_running
        attempt = lease.created.ticket.attempt
        failure = SchedulerTaskFailure.create(
            task_ref=task.task_ref,
            attempt_ref=attempt.attempt_ref,
            error_type=classification.error_type,
            message=classification.message,
            retryable=classification.retryable,
            failed_at=finished_at,
            evidence_refs=classification.evidence_refs,
        )
        failure_outcome = task.fail_attempt(
            attempt=attempt,
            failure=failure,
            occurred_at=finished_at,
            actor_ref=lease.context.scheduler_ref,
            cause_ref=lease.execution_ref,
        )
        status = (
            SchedulerHandlerExecutionStatus.RETRY_WAIT
            if failure_outcome.retry_scheduled
            else SchedulerHandlerExecutionStatus.FAILED
        )
        return {
            "status": status,
            "handler_result": None,
            "completion": None,
            "failure_outcome": failure_outcome,
            "interruption": None,
            "notice_phase": HandlerLifecyclePhase.FAILED,
            "terminal_ref": failure.failure_ref,
            "error_type": classification.error_type,
            "error_message": classification.message,
        }


async def _cancel_task(task: asyncio.Task[Any]) -> None:
    if not task.done():
        task.cancel()
    with suppress(asyncio.CancelledError, Exception):
        await task


def _classify_best_effort(
    classifier: SchedulerHandlerFailureClassifier,
    error: BaseException,
    lease: SchedulerHandlerExecutionLease[Any],
) -> SchedulerHandlerFailureClassification:
    try:
        classification = classifier.classify(error=error, lease=lease)
    except Exception as classifier_error:
        return SchedulerHandlerFailureClassification(
            error_type="FailureClassifierError",
            message=(
                "classification impossible: "
                f"{type(classifier_error).__name__}"
            ),
            retryable=False,
        )
    if not isinstance(classification, SchedulerHandlerFailureClassification):
        return SchedulerHandlerFailureClassification(
            error_type="FailureClassifierContractError",
            message="le classificateur a produit un contrat invalide",
            retryable=False,
        )
    return classification


async def _close_best_effort(
    closer: SchedulerHandlerCloser,
    handler: SchedulerHandler[Any, Any],
    lease: SchedulerHandlerExecutionLease[Any],
) -> SchedulerHandlerCloseReceipt:
    try:
        await closer.close(handler=handler, lease=lease)
    except Exception as exc:
        return SchedulerHandlerCloseReceipt(
            attempted=True,
            closed=False,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    return SchedulerHandlerCloseReceipt(attempted=True, closed=True)


def _publish_best_effort(
    sink: HandlerInformationSink,
    notice: HandlerLifecycleNotice,
) -> HandlerNoticePublication:
    try:
        sink.publish(notice)
    except Exception as exc:
        return HandlerNoticePublication(
            notice=notice,
            published=False,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    return HandlerNoticePublication(notice=notice, published=True)


def _validate_lease(lease: SchedulerHandlerExecutionLease[Any]) -> None:
    if not isinstance(lease, SchedulerHandlerExecutionLease):
        raise TypeError("lease doit être SchedulerHandlerExecutionLease")
    ticket = lease.created.ticket
    if ticket.task_running.state is not SchedulerTaskState.RUNNING:
        raise SchedulerHandlerExecutionError("la tâche du lease doit être running")
    if ticket.attempt.state.value != "running":
        raise SchedulerHandlerExecutionError("la tentative du lease doit être running")
    if lease.context.attempt_ref != ticket.attempt.attempt_ref:
        raise SchedulerHandlerExecutionError("le contexte et la tentative divergent")


def _notice_attributes(
    lease: SchedulerHandlerExecutionLease[Any],
) -> dict[str, object]:
    ticket = lease.created.ticket
    return {
        "command_ref": ticket.task_running.command_ref,
        "task_ref": ticket.task_running.task_ref,
        "attempt": ticket.attempt.number,
        "handler_ref": ticket.handler_binding.handler_ref,
        "capability_ref": ticket.handler_binding.key.capability_ref,
    }


def _outcome_digest(
    *,
    execution_ref: str,
    status: SchedulerHandlerExecutionStatus,
    terminal_ref: str,
    finished_at: str,
    elapsed_ms: int,
    close_succeeded: bool,
) -> str:
    return _length_prefixed_digest(
        (
            ("execution_ref", execution_ref),
            ("status", status.value),
            ("terminal_ref", terminal_ref),
            ("finished_at", finished_at),
            ("elapsed_ms", elapsed_ms),
            ("close_succeeded", close_succeeded),
        )
    )


def _length_prefixed_digest(items: tuple[tuple[str, object], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in items:
        encoded = f"{name}={value}".encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"sha256:{digest.hexdigest()}"


def _validated_refs(name: str, values: Sequence[str]) -> tuple[str, ...]:
    refs = tuple(values)
    if len(set(refs)) != len(refs):
        raise TypeError(f"{name} contient un doublon")
    for ref in refs:
        _require_typed_ref(name, ref)
    return refs


def _parse_utc(name: str, value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TypeError(f"{name} doit être UTC et finir par Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TypeError(f"{name} est invalide") from exc
    if parsed.tzinfo != timezone.utc:
        raise TypeError(f"{name} doit être UTC")
    return parsed


def _require_non_empty(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} doit être une chaîne non vide")


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise TypeError(f"{name} doit être une référence typée")
    if prefix and not value.startswith(prefix):
        raise TypeError(f"{name} doit commencer par {prefix}")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise TypeError(f"{name} doit être un sha256")


def _bare_digest(value: str) -> str:
    return value.removeprefix("sha256:")


__all__ = (
    "SCHEDULER_HANDLER_EXECUTION_OUTCOME_SCHEMA",
    "SchedulerCancellationSignal",
    "SchedulerHandlerCloseReceipt",
    "SchedulerHandlerCloser",
    "SchedulerHandlerExecutionError",
    "SchedulerHandlerExecutionOutcome",
    "SchedulerHandlerExecutionService",
    "SchedulerHandlerExecutionStatus",
    "SchedulerHandlerFailureClassification",
    "SchedulerHandlerFailureClassifier",
    "SchedulerHandlerResultProjection",
    "SchedulerHandlerResultProjector",
)
