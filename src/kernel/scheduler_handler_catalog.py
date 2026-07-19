from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, TypeAlias

from .scheduler_handler_contract import HandlerDescriptor, SchedulerHandler


SchedulerHandlerType: TypeAlias = type[SchedulerHandler[Any, Any]]


@dataclass(frozen=True, slots=True)
class HandlerCapabilityKey:
    """Clé exacte de résolution d'une capacité de handler Scheduler."""

    command_type: type[Any]
    capability_ref: str
    contract_version: int

    def __post_init__(self) -> None:
        if not isinstance(self.command_type, type):
            raise TypeError("command_type doit être une classe")
        if not isinstance(self.capability_ref, str) or not self.capability_ref.startswith(
            "capability:"
        ):
            raise TypeError("capability_ref doit commencer par capability:")
        if not isinstance(self.contract_version, int) or self.contract_version <= 0:
            raise TypeError("contract_version doit être un entier strictement positif")


@dataclass(frozen=True, slots=True)
class SchedulerHandlerBinding:
    """Association immuable entre un contrat de capacité et une classe de handler."""

    key: HandlerCapabilityKey
    handler_ref: str
    handler_type: SchedulerHandlerType
    descriptor: HandlerDescriptor

    @classmethod
    def from_handler_type(
        cls,
        handler_type: SchedulerHandlerType,
    ) -> SchedulerHandlerBinding:
        if not isinstance(handler_type, type) or not issubclass(
            handler_type, SchedulerHandler
        ):
            raise TypeError("handler_type doit hériter de SchedulerHandler")
        descriptor = handler_type.descriptor()
        key = HandlerCapabilityKey(
            command_type=descriptor.command_type,
            capability_ref=descriptor.capability_ref,
            contract_version=descriptor.contract_version,
        )
        return cls(
            key=key,
            handler_ref=descriptor.handler_ref,
            handler_type=handler_type,
            descriptor=descriptor,
        )

    def __post_init__(self) -> None:
        if not self.handler_ref.startswith("handler:"):
            raise TypeError("handler_ref doit commencer par handler:")
        if self.handler_type.descriptor() is not self.descriptor:
            raise TypeError("descriptor doit être celui certifié par handler_type")
        if self.descriptor.handler_ref != self.handler_ref:
            raise TypeError("handler_ref diverge du descripteur")
        if self.descriptor.command_type is not self.key.command_type:
            raise TypeError("command_type diverge du descripteur")
        if self.descriptor.capability_ref != self.key.capability_ref:
            raise TypeError("capability_ref diverge du descripteur")
        if self.descriptor.contract_version != self.key.contract_version:
            raise TypeError("contract_version diverge du descripteur")


class SchedulerHandlerCatalog:
    """Catalogue immuable construit explicitement au bootstrap.

    Il ne possède aucun cycle de vie, n'instancie aucun handler et n'enregistre
    rien par effet d'import. Le Scheduler l'utilisera plus tard comme vue de
    résolution statique, puis conservera toutes les décisions dynamiques.
    """

    __slots__ = ("_by_key", "_by_handler_ref")

    def __init__(self, handler_types: Iterable[SchedulerHandlerType] = ()) -> None:
        by_key: dict[HandlerCapabilityKey, SchedulerHandlerBinding] = {}
        by_handler_ref: dict[str, SchedulerHandlerBinding] = {}
        for handler_type in tuple(handler_types):
            binding = SchedulerHandlerBinding.from_handler_type(handler_type)
            previous_key = by_key.get(binding.key)
            if previous_key is not None:
                raise ValueError(
                    "capacité de handler déjà cataloguée: "
                    f"{binding.key.capability_ref} v{binding.key.contract_version} "
                    f"pour {binding.key.command_type.__qualname__} "
                    f"({previous_key.handler_ref}, {binding.handler_ref})"
                )
            previous_ref = by_handler_ref.get(binding.handler_ref)
            if previous_ref is not None:
                raise ValueError(
                    "handler_ref déjà catalogué: "
                    f"{binding.handler_ref} "
                    f"({previous_ref.key.capability_ref}, {binding.key.capability_ref})"
                )
            by_key[binding.key] = binding
            by_handler_ref[binding.handler_ref] = binding
        self._by_key: Mapping[HandlerCapabilityKey, SchedulerHandlerBinding] = (
            MappingProxyType(by_key)
        )
        self._by_handler_ref: Mapping[str, SchedulerHandlerBinding] = (
            MappingProxyType(by_handler_ref)
        )

    def __len__(self) -> int:
        return len(self._by_key)

    def __iter__(self) -> Iterator[SchedulerHandlerBinding]:
        return iter(self._by_key.values())

    def resolve(
        self,
        *,
        command_type: type[Any],
        capability_ref: str,
        contract_version: int,
    ) -> SchedulerHandlerBinding:
        key = HandlerCapabilityKey(
            command_type=command_type,
            capability_ref=capability_ref,
            contract_version=contract_version,
        )
        try:
            return self._by_key[key]
        except KeyError as exc:
            raise LookupError(
                "aucun handler catalogué pour "
                f"{command_type.__qualname__} / {capability_ref} / v{contract_version}"
            ) from exc

    def resolve_for(
        self,
        command: object,
        *,
        capability_ref: str,
        contract_version: int,
    ) -> SchedulerHandlerBinding:
        return self.resolve(
            command_type=type(command),
            capability_ref=capability_ref,
            contract_version=contract_version,
        )

    def by_handler_ref(self, handler_ref: str) -> SchedulerHandlerBinding:
        try:
            return self._by_handler_ref[handler_ref]
        except KeyError as exc:
            raise LookupError(f"handler inconnu: {handler_ref}") from exc

    def snapshot(self) -> tuple[SchedulerHandlerBinding, ...]:
        return tuple(self._by_key.values())


__all__ = (
    "HandlerCapabilityKey",
    "SchedulerHandlerBinding",
    "SchedulerHandlerCatalog",
    "SchedulerHandlerType",
)
