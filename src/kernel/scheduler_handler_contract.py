from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from inspect import iscoroutinefunction
from string import Formatter
from types import MappingProxyType
from typing import Any, ClassVar, Generic, Protocol, TypeVar


CommandT = TypeVar("CommandT")
ResultT = TypeVar("ResultT")


class HandlerLifecyclePhase(str, Enum):
    """Phases observables du cycle de vie d'un handler Scheduler."""

    DECLARED = "declared"
    CREATED = "created"
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class HandlerNoticeLevel(str, Enum):
    """Niveau sémantique d'un texte informatif de handler."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class HandlerIdempotencyKind(str, Enum):
    """Nature déclarée du rejeu d'un handler."""

    IDEMPOTENT = "idempotent"
    DEDUPLICATED = "deduplicated"
    NON_IDEMPOTENT = "non-idempotent"


_ALLOWED_TEMPLATE_FIELDS = frozenset(
    {
        "handler_ref",
        "capability_ref",
        "handler_title",
        "command_ref",
        "task_ref",
        "result_ref",
        "elapsed_ms",
        "attempt",
        "error_type",
        "error_message",
    }
)


@dataclass(frozen=True, slots=True)
class HandlerExecutionPolicy:
    """Attributs avancés décrivant l'exécution sans l'orchestrer."""

    idempotency: HandlerIdempotencyKind
    timeout_policy_ref: str
    retry_policy_ref: str
    resource_profile_ref: str
    laboratory_compatibility: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("timeout_policy_ref", self.timeout_policy_ref, "timeout-policy:")
        _require_typed_ref("retry_policy_ref", self.retry_policy_ref, "retry-policy:")
        _require_typed_ref("resource_profile_ref", self.resource_profile_ref, "resource-profile:")
        compatibilities = tuple(dict.fromkeys(self.laboratory_compatibility))
        for value in compatibilities:
            _require_typed_ref("laboratory_compatibility", value, "laboratory-kind:")
        object.__setattr__(self, "laboratory_compatibility", compatibilities)


@dataclass(frozen=True, slots=True)
class HandlerInformation:
    """Textes déclaratifs rendus par un rapporteur injecté, jamais par la métaclasse."""

    title: str
    summary: str
    created_text: str = "{handler_title} est prêt."
    started_text: str = "Démarrage de {handler_title} pour {command_ref}."
    succeeded_text: str = "{handler_title} terminé pour {command_ref} en {elapsed_ms} ms."
    failed_text: str = "Échec de {handler_title} pour {command_ref}: {error_type}."
    cancelled_text: str = "{handler_title} annulé pour {command_ref}."
    closed_text: str = "{handler_title} est fermé."

    def __post_init__(self) -> None:
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        for name, template in self.templates().items():
            _require_non_empty(name, template)
            unknown = _template_fields(template) - _ALLOWED_TEMPLATE_FIELDS
            if unknown:
                raise TypeError(
                    f"{name} utilise des attributs informatifs inconnus: "
                    + ", ".join(sorted(unknown))
                )

    def templates(self) -> Mapping[str, str]:
        return MappingProxyType(
            {
                HandlerLifecyclePhase.CREATED.value: self.created_text,
                HandlerLifecyclePhase.STARTED.value: self.started_text,
                HandlerLifecyclePhase.SUCCEEDED.value: self.succeeded_text,
                HandlerLifecyclePhase.FAILED.value: self.failed_text,
                HandlerLifecyclePhase.CANCELLED.value: self.cancelled_text,
                HandlerLifecyclePhase.CLOSED.value: self.closed_text,
            }
        )

    def render(
        self,
        phase: HandlerLifecyclePhase,
        attributes: Mapping[str, object],
    ) -> str:
        if phase is HandlerLifecyclePhase.DECLARED:
            return f"Handler déclaré: {self.title}. {self.summary}"
        template = self.templates()[phase.value]
        values = {name: "" for name in _ALLOWED_TEMPLATE_FIELDS}
        values.update({key: str(value) for key, value in attributes.items() if key in values})
        values["handler_title"] = self.title
        return template.format_map(values)


@dataclass(frozen=True, slots=True)
class HandlerDescriptor:
    """Description statique certifiée par ``SchedulerHandlerMeta``."""

    handler_ref: str
    capability_ref: str
    command_type: type[Any]
    result_type: type[Any]
    contract_version: int
    execution_policy: HandlerExecutionPolicy
    information: HandlerInformation

    def __post_init__(self) -> None:
        _require_typed_ref("handler_ref", self.handler_ref, "handler:")
        _require_typed_ref("capability_ref", self.capability_ref, "capability:")
        if not isinstance(self.command_type, type):
            raise TypeError("command_type doit être une classe")
        if not isinstance(self.result_type, type):
            raise TypeError("result_type doit être une classe")
        if not isinstance(self.contract_version, int) or self.contract_version <= 0:
            raise TypeError("contract_version doit être un entier strictement positif")

    def notice(
        self,
        phase: HandlerLifecyclePhase,
        *,
        level: HandlerNoticeLevel | None = None,
        attributes: Mapping[str, object] | None = None,
    ) -> HandlerLifecycleNotice:
        values = dict(attributes or {})
        values.setdefault("handler_ref", self.handler_ref)
        values.setdefault("capability_ref", self.capability_ref)
        return HandlerLifecycleNotice(
            handler_ref=self.handler_ref,
            capability_ref=self.capability_ref,
            phase=phase,
            level=level or _default_level(phase),
            text=self.information.render(phase, values),
            attributes=MappingProxyType(values),
        )


@dataclass(frozen=True, slots=True)
class HandlerLifecycleNotice:
    """Information structurée publiable vers texte, logs, EventBus ou VisPy."""

    handler_ref: str
    capability_ref: str
    phase: HandlerLifecyclePhase
    level: HandlerNoticeLevel
    text: str
    attributes: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({}),
        compare=False,
    )

    def __post_init__(self) -> None:
        _require_typed_ref("handler_ref", self.handler_ref, "handler:")
        _require_typed_ref("capability_ref", self.capability_ref, "capability:")
        _require_non_empty("text", self.text)
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


class HandlerInformationSink(Protocol):
    """Port d'observation; il n'influence jamais la décision du Scheduler."""

    def publish(self, notice: HandlerLifecycleNotice) -> None:
        """Publie une information de cycle de vie."""


@dataclass(slots=True)
class TextHandlerInformationSink:
    """Adaptateur texte injecté; aucun ``print`` implicite n'est caché dans le noyau."""

    write_line: Callable[[str], None]

    def publish(self, notice: HandlerLifecycleNotice) -> None:
        self.write_line(
            f"[{notice.level.value}] [{notice.phase.value}] "
            f"{notice.handler_ref} — {notice.text}"
        )


class SchedulerHandlerMeta(ABCMeta):
    """Métaclasse de validation et de description, jamais de lancement."""

    _REQUIRED_ATTRIBUTES = (
        "HANDLER_REF",
        "CAPABILITY_REF",
        "COMMAND_TYPE",
        "RESULT_TYPE",
        "CONTRACT_VERSION",
        "EXECUTION_POLICY",
        "INFORMATION",
    )

    def __new__(
        mcls,
        name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> SchedulerHandlerMeta:
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        if namespace.get("ABSTRACT_HANDLER", False):
            return cls

        missing = [
            attribute
            for attribute in mcls._REQUIRED_ATTRIBUTES
            if attribute not in namespace
        ]
        if missing:
            raise TypeError(
                f"{name} doit déclarer explicitement: " + ", ".join(missing)
            )
        if not iscoroutinefunction(getattr(cls, "execute", None)):
            raise TypeError(f"{name}.execute doit être asynchrone")
        policy = namespace["EXECUTION_POLICY"]
        information = namespace["INFORMATION"]
        if not isinstance(policy, HandlerExecutionPolicy):
            raise TypeError("EXECUTION_POLICY doit être HandlerExecutionPolicy")
        if not isinstance(information, HandlerInformation):
            raise TypeError("INFORMATION doit être HandlerInformation")

        descriptor = HandlerDescriptor(
            handler_ref=str(namespace["HANDLER_REF"]),
            capability_ref=str(namespace["CAPABILITY_REF"]),
            command_type=namespace["COMMAND_TYPE"],  # type: ignore[arg-type]
            result_type=namespace["RESULT_TYPE"],  # type: ignore[arg-type]
            contract_version=namespace["CONTRACT_VERSION"],  # type: ignore[arg-type]
            execution_policy=policy,
            information=information,
        )
        setattr(cls, "__handler_descriptor__", descriptor)
        return cls


class SchedulerHandler(
    Generic[CommandT, ResultT],
    ABC,
    metaclass=SchedulerHandlerMeta,
):
    """Classe abstraite des capacités exécutables sous autorité du Scheduler."""

    ABSTRACT_HANDLER = True

    HANDLER_REF: ClassVar[str]
    CAPABILITY_REF: ClassVar[str]
    COMMAND_TYPE: ClassVar[type[Any]]
    RESULT_TYPE: ClassVar[type[Any]]
    CONTRACT_VERSION: ClassVar[int]
    EXECUTION_POLICY: ClassVar[HandlerExecutionPolicy]
    INFORMATION: ClassVar[HandlerInformation]
    __handler_descriptor__: ClassVar[HandlerDescriptor]

    @classmethod
    def descriptor(cls) -> HandlerDescriptor:
        try:
            return cls.__handler_descriptor__
        except AttributeError as exc:
            raise TypeError("un handler abstrait ne possède pas de descripteur concret") from exc

    @classmethod
    def lifecycle_notice(
        cls,
        phase: HandlerLifecyclePhase,
        *,
        level: HandlerNoticeLevel | None = None,
        **attributes: object,
    ) -> HandlerLifecycleNotice:
        return cls.descriptor().notice(
            phase,
            level=level,
            attributes=attributes,
        )

    @abstractmethod
    async def execute(self, command: CommandT, context: object) -> ResultT:
        """Exécute une capacité; le Scheduler conserve l'orchestration."""
        raise NotImplementedError


def _template_fields(template: str) -> frozenset[str]:
    return frozenset(
        field_name
        for _literal, field_name, _format_spec, _conversion in Formatter().parse(template)
        if field_name is not None
    )


def _default_level(phase: HandlerLifecyclePhase) -> HandlerNoticeLevel:
    if phase is HandlerLifecyclePhase.FAILED:
        return HandlerNoticeLevel.ERROR
    if phase in {HandlerLifecyclePhase.CANCELLED, HandlerLifecyclePhase.CLOSED}:
        return HandlerNoticeLevel.WARNING
    if phase is HandlerLifecyclePhase.DECLARED:
        return HandlerNoticeLevel.DEBUG
    return HandlerNoticeLevel.INFO


def _require_non_empty(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} doit être une chaîne non vide")


def _require_typed_ref(name: str, value: object, prefix: str) -> None:
    _require_non_empty(name, value)
    if not str(value).startswith(prefix):
        raise TypeError(f"{name} doit commencer par {prefix}")


__all__ = (
    "HandlerDescriptor",
    "HandlerExecutionPolicy",
    "HandlerIdempotencyKind",
    "HandlerInformation",
    "HandlerInformationSink",
    "HandlerLifecycleNotice",
    "HandlerLifecyclePhase",
    "HandlerNoticeLevel",
    "SchedulerHandler",
    "SchedulerHandlerMeta",
    "TextHandlerInformationSink",
)
