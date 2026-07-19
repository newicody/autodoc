"""Création et armement contrôlés des instances de handlers Scheduler.

Cette frontière consomme un ``SchedulerHandlerLaunchTicket`` déjà commité et
une fabrique explicitement injectée. Elle construit réellement l'instance,
publie au mieux les notices informatives ``CREATED`` puis ``STARTED`` et
produit un contexte typé pour l'exécuteur suivant.

Elle n'appelle jamais ``handler.execute()``. Elle ne décide ni priorité, ni
reprise, ni tâche suivante et ne publie aucune commande sur Dispatcher ou
EventBus. Un échec du canal d'information reste observation-only et ne peut
pas annuler une décision durable du Scheduler.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import re
from types import MappingProxyType
from typing import Any, Generic, Protocol, TypeAlias, TypeVar, runtime_checkable

from .scheduler_handler_catalog import SchedulerHandlerBinding
from .scheduler_handler_contract import (
    HandlerInformationSink,
    HandlerLifecycleNotice,
    HandlerLifecyclePhase,
    SchedulerHandler,
)
from .scheduler_task_launch_preparation import SchedulerHandlerLaunchTicket
from .scheduler_task_model import SchedulerTaskState


CommandT = TypeVar("CommandT")

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

SCHEDULER_HANDLER_INSTANCE_CREATED_SCHEMA = (
    "missipy.scheduler.handler_instance_created.v1"
)
SCHEDULER_HANDLER_EXECUTION_LEASE_SCHEMA = (
    "missipy.scheduler.handler_execution_lease.v1"
)


class SchedulerHandlerInstanceLifecycleError(RuntimeError):
    """Erreur de construction ou d'armement d'une instance de handler."""


HandlerBuilder: TypeAlias = Callable[
    [SchedulerHandlerBinding, SchedulerHandlerLaunchTicket[Any]],
    SchedulerHandler[Any, Any],
]


@runtime_checkable
class SchedulerHandlerFactory(Protocol):
    """Fabrique injectée; elle ne choisit pas le handler à la place du Scheduler."""

    def create(
        self,
        *,
        binding: SchedulerHandlerBinding,
        ticket: SchedulerHandlerLaunchTicket[Any],
    ) -> SchedulerHandler[Any, Any]: ...


class ExplicitSchedulerHandlerFactory:
    """Fabrique immuable de builders explicitement assemblés au bootstrap."""

    __slots__ = ("_builders",)

    def __init__(self, builders: Mapping[str, HandlerBuilder]) -> None:
        copied: dict[str, HandlerBuilder] = {}
        for handler_ref, builder in dict(builders).items():
            _require_typed_ref("handler_ref", handler_ref, "handler:")
            if not callable(builder):
                raise TypeError(f"builder non appelable pour {handler_ref}")
            copied[handler_ref] = builder
        self._builders: Mapping[str, HandlerBuilder] = MappingProxyType(copied)

    def create(
        self,
        *,
        binding: SchedulerHandlerBinding,
        ticket: SchedulerHandlerLaunchTicket[Any],
    ) -> SchedulerHandler[Any, Any]:
        try:
            builder = self._builders[binding.handler_ref]
        except KeyError as exc:
            raise SchedulerHandlerInstanceLifecycleError(
                f"aucun builder injecté pour {binding.handler_ref}"
            ) from exc
        instance = builder(binding, ticket)
        if not isinstance(instance, binding.handler_type):
            raise SchedulerHandlerInstanceLifecycleError(
                "le builder a produit un type de handler divergent"
            )
        if instance.descriptor() is not binding.descriptor:
            raise SchedulerHandlerInstanceLifecycleError(
                "le descripteur de l'instance diverge du binding"
            )
        return instance


@dataclass(frozen=True, slots=True)
class HandlerNoticePublication:
    """Résultat observation-only d'une tentative de publication informative."""

    notice: HandlerLifecycleNotice
    published: bool
    error_type: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        if self.published and (self.error_type or self.error_message):
            raise TypeError("une publication réussie ne porte pas d'erreur")
        if not self.published and not self.error_type:
            raise TypeError("une publication échouée exige error_type")


@dataclass(frozen=True, slots=True)
class SchedulerHandlerExecutionContext:
    """Contexte léger remis plus tard à ``handler.execute`` par le Scheduler."""

    scheduler_ref: str
    command_ref: str
    task_ref: str
    attempt_ref: str
    reservation_ref: str
    launch_ticket_ref: str
    handler_instance_ref: str
    deadline_at: str
    started_at: str

    def __post_init__(self) -> None:
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _require_typed_ref("command_ref", self.command_ref, "scheduler-command:")
        _require_typed_ref("task_ref", self.task_ref, "scheduler-task:")
        _require_typed_ref("attempt_ref", self.attempt_ref, "scheduler-attempt:")
        _require_typed_ref(
            "reservation_ref", self.reservation_ref, "scheduler-reservation:"
        )
        _require_typed_ref(
            "launch_ticket_ref", self.launch_ticket_ref, "scheduler-handler-launch:"
        )
        _require_typed_ref(
            "handler_instance_ref", self.handler_instance_ref, "handler-instance:"
        )
        deadline = _parse_utc("deadline_at", self.deadline_at)
        started = _parse_utc("started_at", self.started_at)
        if started >= deadline:
            raise SchedulerHandlerInstanceLifecycleError(
                "started_at doit précéder deadline_at"
            )


@dataclass(frozen=True, slots=True)
class SchedulerHandlerInstanceCreated(Generic[CommandT]):
    """Preuve qu'une instance réelle existe après le commit durable du lancement."""

    schema: str
    instance_ref: str
    ticket: SchedulerHandlerLaunchTicket[CommandT] = field(repr=False)
    handler: SchedulerHandler[CommandT, Any] = field(repr=False, compare=False)
    created_at: str
    created_notice: HandlerLifecycleNotice
    publication: HandlerNoticePublication
    instance_digest: str

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_HANDLER_INSTANCE_CREATED_SCHEMA:
            raise SchedulerHandlerInstanceLifecycleError(
                "unsupported Scheduler handler instance schema"
            )
        _require_typed_ref("instance_ref", self.instance_ref, "handler-instance:")
        created = _parse_utc("created_at", self.created_at)
        committed = _parse_utc(
            "launch_commit.committed_at", self.ticket.launch_commit.committed_at
        )
        deadline = _parse_utc("attempt.deadline_at", self.ticket.attempt.deadline_at)
        if created < committed:
            raise SchedulerHandlerInstanceLifecycleError(
                "created_at ne peut pas précéder le commit durable"
            )
        if created >= deadline:
            raise SchedulerHandlerInstanceLifecycleError(
                "la création du handler dépasse la deadline de tentative"
            )
        if self.ticket.task_running.state is not SchedulerTaskState.RUNNING:
            raise SchedulerHandlerInstanceLifecycleError(
                "le ticket doit porter une tâche running"
            )
        binding = self.ticket.handler_binding
        if not isinstance(self.handler, binding.handler_type):
            raise SchedulerHandlerInstanceLifecycleError(
                "l'instance ne correspond pas au handler résolu"
            )
        if self.created_notice.phase is not HandlerLifecyclePhase.CREATED:
            raise SchedulerHandlerInstanceLifecycleError(
                "created_notice doit être CREATED"
            )
        if self.publication.notice is not self.created_notice:
            raise SchedulerHandlerInstanceLifecycleError(
                "la publication doit référencer created_notice"
            )
        _require_sha256("instance_digest", self.instance_digest)
        expected = _instance_digest(
            ticket_ref=self.ticket.ticket_ref,
            handler_ref=binding.handler_ref,
            task_ref=self.ticket.task_running.task_ref,
            attempt_ref=self.ticket.attempt.attempt_ref,
            created_at=self.created_at,
        )
        if self.instance_digest != expected:
            raise SchedulerHandlerInstanceLifecycleError(
                "instance_digest incohérent"
            )
        expected_ref = f"handler-instance:{_bare_digest(expected)[:24]}"
        if self.instance_ref != expected_ref:
            raise SchedulerHandlerInstanceLifecycleError("instance_ref incohérent")


@dataclass(frozen=True, slots=True)
class SchedulerHandlerExecutionLease(Generic[CommandT]):
    """Instance armée pour l'exécuteur suivant; la capacité n'est pas appelée."""

    schema: str
    execution_ref: str
    created: SchedulerHandlerInstanceCreated[CommandT] = field(repr=False)
    context: SchedulerHandlerExecutionContext
    started_notice: HandlerLifecycleNotice
    publication: HandlerNoticePublication
    execution_digest: str

    def __post_init__(self) -> None:
        if self.schema != SCHEDULER_HANDLER_EXECUTION_LEASE_SCHEMA:
            raise SchedulerHandlerInstanceLifecycleError(
                "unsupported Scheduler handler execution lease schema"
            )
        _require_typed_ref("execution_ref", self.execution_ref, "handler-execution:")
        if self.context.handler_instance_ref != self.created.instance_ref:
            raise SchedulerHandlerInstanceLifecycleError(
                "le contexte diverge de l'instance créée"
            )
        if self.started_notice.phase is not HandlerLifecyclePhase.STARTED:
            raise SchedulerHandlerInstanceLifecycleError(
                "started_notice doit être STARTED"
            )
        if self.publication.notice is not self.started_notice:
            raise SchedulerHandlerInstanceLifecycleError(
                "la publication doit référencer started_notice"
            )
        _require_sha256("execution_digest", self.execution_digest)
        expected = _execution_digest(
            instance_ref=self.created.instance_ref,
            ticket_ref=self.created.ticket.ticket_ref,
            task_ref=self.context.task_ref,
            attempt_ref=self.context.attempt_ref,
            started_at=self.context.started_at,
        )
        if self.execution_digest != expected:
            raise SchedulerHandlerInstanceLifecycleError(
                "execution_digest incohérent"
            )
        expected_ref = f"handler-execution:{_bare_digest(expected)[:24]}"
        if self.execution_ref != expected_ref:
            raise SchedulerHandlerInstanceLifecycleError("execution_ref incohérent")


class SchedulerHandlerInstanceLifecycleService:
    """Construit puis arme un handler sans exécuter sa capacité métier."""

    def create(
        self,
        *,
        ticket: SchedulerHandlerLaunchTicket[CommandT],
        factory: SchedulerHandlerFactory,
        information_sink: HandlerInformationSink,
        created_at: str,
    ) -> SchedulerHandlerInstanceCreated[CommandT]:
        _validate_ticket(ticket)
        _parse_utc("created_at", created_at)
        binding = ticket.handler_binding
        attributes = _notice_attributes(ticket)
        try:
            handler = factory.create(binding=binding, ticket=ticket)
        except Exception as exc:
            failed = binding.descriptor.notice(
                HandlerLifecyclePhase.FAILED,
                attributes={
                    **attributes,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            _publish_best_effort(information_sink, failed)
            raise SchedulerHandlerInstanceLifecycleError(
                f"création impossible de {binding.handler_ref}: {type(exc).__name__}"
            ) from exc
        digest = _instance_digest(
            ticket_ref=ticket.ticket_ref,
            handler_ref=binding.handler_ref,
            task_ref=ticket.task_running.task_ref,
            attempt_ref=ticket.attempt.attempt_ref,
            created_at=created_at,
        )
        notice = binding.descriptor.notice(
            HandlerLifecyclePhase.CREATED,
            attributes=attributes,
        )
        publication = _publish_best_effort(information_sink, notice)
        return SchedulerHandlerInstanceCreated(
            schema=SCHEDULER_HANDLER_INSTANCE_CREATED_SCHEMA,
            instance_ref=f"handler-instance:{_bare_digest(digest)[:24]}",
            ticket=ticket,
            handler=handler,
            created_at=created_at,
            created_notice=notice,
            publication=publication,
            instance_digest=digest,
        )

    def start(
        self,
        *,
        created: SchedulerHandlerInstanceCreated[CommandT],
        information_sink: HandlerInformationSink,
        started_at: str,
    ) -> SchedulerHandlerExecutionLease[CommandT]:
        started = _parse_utc("started_at", started_at)
        created_time = _parse_utc("created_at", created.created_at)
        deadline = _parse_utc(
            "attempt.deadline_at", created.ticket.attempt.deadline_at
        )
        if started < created_time:
            raise SchedulerHandlerInstanceLifecycleError(
                "started_at ne peut pas précéder created_at"
            )
        if started >= deadline:
            raise SchedulerHandlerInstanceLifecycleError(
                "la deadline de tentative est expirée avant STARTED"
            )
        ticket = created.ticket
        context = SchedulerHandlerExecutionContext(
            scheduler_ref=ticket.scheduler_ref,
            command_ref=ticket.task_running.command_ref,
            task_ref=ticket.task_running.task_ref,
            attempt_ref=ticket.attempt.attempt_ref,
            reservation_ref=ticket.reservation.reservation_ref,
            launch_ticket_ref=ticket.ticket_ref,
            handler_instance_ref=created.instance_ref,
            deadline_at=ticket.attempt.deadline_at,
            started_at=started_at,
        )
        attributes = _notice_attributes(ticket)
        notice = ticket.handler_binding.descriptor.notice(
            HandlerLifecyclePhase.STARTED,
            attributes=attributes,
        )
        publication = _publish_best_effort(information_sink, notice)
        digest = _execution_digest(
            instance_ref=created.instance_ref,
            ticket_ref=ticket.ticket_ref,
            task_ref=context.task_ref,
            attempt_ref=context.attempt_ref,
            started_at=started_at,
        )
        return SchedulerHandlerExecutionLease(
            schema=SCHEDULER_HANDLER_EXECUTION_LEASE_SCHEMA,
            execution_ref=f"handler-execution:{_bare_digest(digest)[:24]}",
            created=created,
            context=context,
            started_notice=notice,
            publication=publication,
            execution_digest=digest,
        )


def _validate_ticket(ticket: SchedulerHandlerLaunchTicket[Any]) -> None:
    if not isinstance(ticket, SchedulerHandlerLaunchTicket):
        raise TypeError("ticket doit être SchedulerHandlerLaunchTicket")
    if ticket.task_running.state is not SchedulerTaskState.RUNNING:
        raise SchedulerHandlerInstanceLifecycleError(
            "le ticket doit porter une tâche running"
        )
    if not ticket.launch_commit.transaction_ref:
        raise SchedulerHandlerInstanceLifecycleError(
            "la création exige un commit durable"
        )
    if type(ticket.command) is not ticket.handler_binding.key.command_type:
        raise SchedulerHandlerInstanceLifecycleError(
            "le type de commande diverge du handler résolu"
        )


def _notice_attributes(
    ticket: SchedulerHandlerLaunchTicket[Any],
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "command_ref": ticket.task_running.command_ref,
            "task_ref": ticket.task_running.task_ref,
            "attempt": ticket.attempt.number,
            "handler_ref": ticket.handler_binding.handler_ref,
            "capability_ref": ticket.handler_binding.key.capability_ref,
        }
    )


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


def _instance_digest(
    *,
    ticket_ref: str,
    handler_ref: str,
    task_ref: str,
    attempt_ref: str,
    created_at: str,
) -> str:
    return _length_prefixed_digest(
        (
            ("ticket_ref", ticket_ref),
            ("handler_ref", handler_ref),
            ("task_ref", task_ref),
            ("attempt_ref", attempt_ref),
            ("created_at", created_at),
        )
    )


def _execution_digest(
    *,
    instance_ref: str,
    ticket_ref: str,
    task_ref: str,
    attempt_ref: str,
    started_at: str,
) -> str:
    return _length_prefixed_digest(
        (
            ("instance_ref", instance_ref),
            ("ticket_ref", ticket_ref),
            ("task_ref", task_ref),
            ("attempt_ref", attempt_ref),
            ("started_at", started_at),
        )
    )


def _length_prefixed_digest(items: tuple[tuple[str, object], ...]) -> str:
    digest = hashlib.sha256()
    for name, value in items:
        encoded = f"{name}={value}".encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return f"sha256:{digest.hexdigest()}"


def _bare_digest(value: str) -> str:
    return value.split(":", 1)[1]


def _parse_utc(name: str, value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TypeError(f"{name} doit être un horodatage UTC terminé par Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise TypeError(f"{name} est invalide") from exc
    if parsed.tzinfo != timezone.utc:
        raise TypeError(f"{name} doit être UTC")
    return parsed


def _require_typed_ref(name: str, value: object, prefix: str) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise TypeError(f"{name} doit être une référence typée")
    if not value.startswith(prefix):
        raise TypeError(f"{name} doit commencer par {prefix}")


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise TypeError(f"{name} doit être un sha256 préfixé")


__all__ = (
    "ExplicitSchedulerHandlerFactory",
    "HandlerBuilder",
    "HandlerNoticePublication",
    "SchedulerHandlerExecutionContext",
    "SchedulerHandlerExecutionLease",
    "SchedulerHandlerFactory",
    "SchedulerHandlerInstanceCreated",
    "SchedulerHandlerInstanceLifecycleError",
    "SchedulerHandlerInstanceLifecycleService",
)
