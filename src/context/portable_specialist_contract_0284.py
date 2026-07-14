"""Immutable portable-specialist contracts for phase 0284-r2.

A portable specialist keeps one stable identity while being declared compatible
with one or more laboratory frameworks.  This module contains contracts and
pure validation only.  It does not instantiate a specialist, attach a provider,
register a runtime component, alter Scheduler.run(), publish on EventBus, touch
/dev/shm, access SQL/Qdrant, call OpenVINO, call GitHub, or import a laboratory
implementation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import re
from typing import Literal

PORTABLE_SPECIALIST_CONTRACT_VERSION = "0284.r2"
SPECIALIST_CAPABILITY_SCHEMA = "missipy.specialist.capability.v1"
SPECIALIST_EXECUTION_PROFILE_SCHEMA = "missipy.specialist.execution_profile.v1"
SPECIALIST_LABORATORY_BINDING_SCHEMA = "missipy.specialist.laboratory_binding.v1"
PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA = "missipy.specialist.descriptor.v1"

SpecialistAvailability = Literal[
    "declared",
    "disabled",
    "unavailable",
    "ready",
]
SpecialistExecutionBoundary = Literal[
    "in_process",
    "local_process",
    "remote_service",
]
SpecialistLaboratoryVisitMode = Literal[
    "resident",
    "visitor",
    "transfer",
]
SpecialistDeterminismPreference = Literal[
    "required",
    "preferred",
    "not_required",
]

_ALLOWED_AVAILABILITY = frozenset({"declared", "disabled", "unavailable", "ready"})
_ALLOWED_EXECUTION_BOUNDARIES = frozenset(
    {"in_process", "local_process", "remote_service"}
)
_ALLOWED_VISIT_MODES = frozenset({"resident", "visitor", "transfer"})
_ALLOWED_DETERMINISM = frozenset({"required", "preferred", "not_required"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][a-z0-9.-]+)?$")
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_LABORATORY_PREFIXES = ("laboratory:",)
_CONTRACT_PREFIXES = ("contract:",)
_DEVICE_PREFIXES = ("device:", "openvino:", "accelerator:")
_MAX_PARALLEL_VISITS = 1_024
_MAX_EXTERNAL_CALLS = 1_024
_MAX_BINDING_PRIORITY = 10_000


class PortableSpecialistContractError(ValueError):
    """Raised when a portable-specialist contract is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityContract:
    """One declared specialist capability and its contract envelope."""

    schema: str
    capability: str
    description: str
    accepted_input_contract_refs: tuple[str, ...]
    produced_output_contract_refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_SCHEMA:
            raise PortableSpecialistContractError(
                "unsupported specialist capability schema"
            )
        _require_capability(self.capability)
        _require_non_empty("description", self.description)
        object.__setattr__(
            self,
            "accepted_input_contract_refs",
            _normalize_refs(
                "accepted_input_contract_refs",
                self.accepted_input_contract_refs,
                required_prefixes=_CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "produced_output_contract_refs",
            _normalize_refs(
                "produced_output_contract_refs",
                self.produced_output_contract_refs,
                required_prefixes=_CONTRACT_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "capability": self.capability,
            "description": self.description,
            "accepted_input_contract_refs": list(
                self.accepted_input_contract_refs
            ),
            "produced_output_contract_refs": list(
                self.produced_output_contract_refs
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SpecialistExecutionProfile:
    """Portable execution preferences, not a provider or runtime binding."""

    schema: str
    preferred_execution_boundaries: tuple[SpecialistExecutionBoundary, ...]
    determinism_preference: SpecialistDeterminismPreference = "preferred"
    max_parallel_visits: int = 1
    network_allowed: bool = False
    max_external_calls_per_visit: int = 0
    accelerator_required: bool = False
    preferred_device_refs: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_EXECUTION_PROFILE_SCHEMA:
            raise PortableSpecialistContractError(
                "unsupported specialist execution profile schema"
            )
        boundaries = _normalize_literals(
            "preferred_execution_boundaries",
            self.preferred_execution_boundaries,
            allowed=_ALLOWED_EXECUTION_BOUNDARIES,
        )
        if "remote_service" in boundaries and not self.network_allowed:
            raise PortableSpecialistContractError(
                "remote_service preference requires network_allowed"
            )
        object.__setattr__(self, "preferred_execution_boundaries", boundaries)
        if self.determinism_preference not in _ALLOWED_DETERMINISM:
            raise PortableSpecialistContractError(
                "unsupported specialist determinism preference"
            )
        _require_int_range(
            "max_parallel_visits",
            self.max_parallel_visits,
            minimum=1,
            maximum=_MAX_PARALLEL_VISITS,
        )
        _require_int_range(
            "max_external_calls_per_visit",
            self.max_external_calls_per_visit,
            minimum=0,
            maximum=_MAX_EXTERNAL_CALLS,
        )
        if not self.network_allowed and self.max_external_calls_per_visit != 0:
            raise PortableSpecialistContractError(
                "max_external_calls_per_visit must be 0 when network is disabled"
            )
        device_refs = _normalize_refs(
            "preferred_device_refs",
            self.preferred_device_refs,
            allow_empty=True,
            required_prefixes=_DEVICE_PREFIXES,
        )
        if self.accelerator_required and not device_refs:
            raise PortableSpecialistContractError(
                "accelerator_required needs at least one preferred_device_ref"
            )
        object.__setattr__(self, "preferred_device_refs", device_refs)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "preferred_execution_boundaries": list(
                self.preferred_execution_boundaries
            ),
            "determinism_preference": self.determinism_preference,
            "max_parallel_visits": self.max_parallel_visits,
            "network_allowed": self.network_allowed,
            "max_external_calls_per_visit": self.max_external_calls_per_visit,
            "accelerator_required": self.accelerator_required,
            "preferred_device_refs": list(self.preferred_device_refs),
            "metadata": dict(self.metadata),
            "provider_instantiated": False,
            "runtime_attached": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistLaboratoryBinding:
    """Declared compatibility between one specialist and one laboratory."""

    schema: str
    specialist_ref: str
    laboratory_ref: str
    visit_modes: tuple[SpecialistLaboratoryVisitMode, ...]
    required_laboratory_capabilities: tuple[str, ...]
    priority: int = 100
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    provider_bound: bool = field(default=False, init=False)
    runtime_attached: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_LABORATORY_BINDING_SCHEMA:
            raise PortableSpecialistContractError(
                "unsupported specialist laboratory binding schema"
            )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        object.__setattr__(
            self,
            "visit_modes",
            _normalize_literals(
                "visit_modes",
                self.visit_modes,
                allowed=_ALLOWED_VISIT_MODES,
            ),
        )
        object.__setattr__(
            self,
            "required_laboratory_capabilities",
            _normalize_capabilities(self.required_laboratory_capabilities),
        )
        _require_int_range(
            "priority",
            self.priority,
            minimum=0,
            maximum=_MAX_BINDING_PRIORITY,
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "specialist_ref": self.specialist_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_modes": list(self.visit_modes),
            "required_laboratory_capabilities": list(
                self.required_laboratory_capabilities
            ),
            "priority": self.priority,
            "metadata": dict(self.metadata),
            "provider_bound": self.provider_bound,
            "runtime_attached": self.runtime_attached,
        }


@dataclass(frozen=True, slots=True)
class PortableSpecialistDescriptor:
    """Stable specialist identity portable across declared laboratories."""

    schema: str
    specialist_ref: str
    display_name: str
    specialist_version: str
    capabilities: tuple[SpecialistCapabilityContract, ...]
    accepted_input_contract_refs: tuple[str, ...]
    produced_output_contract_refs: tuple[str, ...]
    execution_profile: SpecialistExecutionProfile
    laboratory_bindings: tuple[SpecialistLaboratoryBinding, ...]
    availability: SpecialistAvailability = "declared"
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA:
            raise PortableSpecialistContractError(
                "unsupported portable specialist descriptor schema"
            )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_non_empty("display_name", self.display_name)
        if not isinstance(self.specialist_version, str) or not _VERSION_RE.match(
            self.specialist_version
        ):
            raise PortableSpecialistContractError(
                "specialist_version must be a dotted numeric version"
            )
        capabilities = tuple(self.capabilities)
        if not capabilities or not all(
            isinstance(item, SpecialistCapabilityContract) for item in capabilities
        ):
            raise PortableSpecialistContractError(
                "capabilities must contain SpecialistCapabilityContract values"
            )
        capability_names = tuple(item.capability for item in capabilities)
        if len(set(capability_names)) != len(capability_names):
            raise PortableSpecialistContractError(
                "specialist capabilities must be unique"
            )
        object.__setattr__(self, "capabilities", capabilities)
        accepted = _normalize_refs(
            "accepted_input_contract_refs",
            self.accepted_input_contract_refs,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        produced = _normalize_refs(
            "produced_output_contract_refs",
            self.produced_output_contract_refs,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        object.__setattr__(self, "accepted_input_contract_refs", accepted)
        object.__setattr__(self, "produced_output_contract_refs", produced)
        if not isinstance(self.execution_profile, SpecialistExecutionProfile):
            raise PortableSpecialistContractError(
                "execution_profile must be a SpecialistExecutionProfile"
            )
        bindings = tuple(self.laboratory_bindings)
        if not bindings or not all(
            isinstance(item, SpecialistLaboratoryBinding) for item in bindings
        ):
            raise PortableSpecialistContractError(
                "laboratory_bindings must contain SpecialistLaboratoryBinding values"
            )
        laboratory_refs = tuple(item.laboratory_ref for item in bindings)
        if len(set(laboratory_refs)) != len(laboratory_refs):
            raise PortableSpecialistContractError(
                "laboratory_bindings must contain one binding per laboratory"
            )
        for binding in bindings:
            if binding.specialist_ref != self.specialist_ref:
                raise PortableSpecialistContractError(
                    "laboratory binding specialist_ref must match descriptor"
                )
        object.__setattr__(
            self,
            "laboratory_bindings",
            tuple(sorted(bindings, key=lambda item: (item.priority, item.laboratory_ref))),
        )
        accepted_set = frozenset(accepted)
        produced_set = frozenset(produced)
        for capability in capabilities:
            if not set(capability.accepted_input_contract_refs).issubset(accepted_set):
                raise PortableSpecialistContractError(
                    "capability input contracts must be declared by descriptor"
                )
            if not set(capability.produced_output_contract_refs).issubset(produced_set):
                raise PortableSpecialistContractError(
                    "capability output contracts must be declared by descriptor"
                )
        if self.availability not in _ALLOWED_AVAILABILITY:
            raise PortableSpecialistContractError(
                "unsupported specialist availability"
            )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "specialist_ref": self.specialist_ref,
            "display_name": self.display_name,
            "specialist_version": self.specialist_version,
            "capabilities": [item.to_mapping() for item in self.capabilities],
            "accepted_input_contract_refs": list(
                self.accepted_input_contract_refs
            ),
            "produced_output_contract_refs": list(
                self.produced_output_contract_refs
            ),
            "execution_profile": self.execution_profile.to_mapping(),
            "laboratory_bindings": [
                item.to_mapping() for item in self.laboratory_bindings
            ],
            "availability": self.availability,
            "metadata": dict(self.metadata),
            "stable_identity_portable": True,
            "provider_instantiated": False,
            "runtime_attached": False,
            "scheduler_remains_orchestrator": True,
            "eventbus_observation_only": True,
            "sql_remains_authority": True,
            "qdrant_projection_recall_only": True,
        }


def validate_portable_specialist_visit_contract(
    descriptor: PortableSpecialistDescriptor,
    *,
    specialist_ref: str,
    laboratory_ref: str,
    input_contract_ref: str,
    output_contract_ref: str,
    visit_mode: SpecialistLaboratoryVisitMode,
) -> tuple[str, ...]:
    """Validate route/visit references without importing runtime contracts."""

    issues: list[str] = []
    if specialist_ref != descriptor.specialist_ref:
        issues.append("specialist_ref must match portable descriptor")
    if input_contract_ref not in descriptor.accepted_input_contract_refs:
        issues.append("input_contract_ref is not accepted by specialist")
    if output_contract_ref not in descriptor.produced_output_contract_refs:
        issues.append("output_contract_ref is not produced by specialist")
    binding = next(
        (
            item
            for item in descriptor.laboratory_bindings
            if item.laboratory_ref == laboratory_ref
        ),
        None,
    )
    if binding is None:
        issues.append("laboratory_ref is not declared for specialist")
    elif visit_mode not in binding.visit_modes:
        issues.append("visit_mode is not allowed for laboratory binding")
    return tuple(issues)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PortableSpecialistContractError(f"{name} must be non-empty")


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise PortableSpecialistContractError(f"{name} must be a typed reference")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise PortableSpecialistContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_capability(value: str) -> None:
    if not isinstance(value, str) or not _CAPABILITY_RE.match(value):
        raise PortableSpecialistContractError(
            "capability must use lowercase dotted identifier syntax"
        )


def _require_int_range(
    name: str,
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PortableSpecialistContractError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise PortableSpecialistContractError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values and not allow_empty:
        raise PortableSpecialistContractError(f"{name} must not be empty")
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return tuple(dict.fromkeys(values))


def _normalize_capabilities(values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    )
    if not normalized:
        raise PortableSpecialistContractError(
            "required_laboratory_capabilities must not be empty"
        )
    unique = tuple(dict.fromkeys(normalized))
    for capability in unique:
        _require_capability(capability)
    return unique


def _normalize_literals(
    name: str,
    values: Sequence[str],
    *,
    allowed: frozenset[str],
) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not normalized:
        raise PortableSpecialistContractError(f"{name} must not be empty")
    if any(value not in allowed for value in normalized):
        raise PortableSpecialistContractError(f"unsupported value in {name}")
    return normalized


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(dict(normalized).items())


__all__ = (
    "PORTABLE_SPECIALIST_CONTRACT_VERSION",
    "PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA",
    "SPECIALIST_CAPABILITY_SCHEMA",
    "SPECIALIST_EXECUTION_PROFILE_SCHEMA",
    "SPECIALIST_LABORATORY_BINDING_SCHEMA",
    "PortableSpecialistContractError",
    "PortableSpecialistDescriptor",
    "SpecialistAvailability",
    "SpecialistCapabilityContract",
    "SpecialistDeterminismPreference",
    "SpecialistExecutionBoundary",
    "SpecialistExecutionProfile",
    "SpecialistLaboratoryBinding",
    "SpecialistLaboratoryVisitMode",
    "validate_portable_specialist_visit_contract",
)
