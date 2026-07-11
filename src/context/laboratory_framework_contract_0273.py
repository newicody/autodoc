"""Versioned laboratory framework contracts for phase 0273-r2.

A laboratory is a bounded execution framework for specialists.  This module
adds only immutable and serializable contracts plus a declarative binding plan
for the existing Scheduler-owned runtime registry.

It does not instantiate a provider, create a manager, attach a registry,
alter the Scheduler loop, publish on EventBus, access RouteProxy/ControlProxy,
write SQL/Qdrant, call GitHub, import VisPy, or import a GenAI framework.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Any, Literal

LABORATORY_FRAMEWORK_CONTRACT_VERSION = "0273.r2"
LABORATORY_DESCRIPTOR_SCHEMA = "missipy.laboratory.descriptor.v1"
LABORATORY_RESOURCE_BUDGET_SCHEMA = "missipy.laboratory.resource_budget.v1"
LABORATORY_VISIT_REQUEST_SCHEMA = "missipy.laboratory.visit_request.v1"
LABORATORY_VISIT_RESULT_SCHEMA = "missipy.laboratory.visit_result.v1"
LABORATORY_REGISTRY_BINDING_SCHEMA = "missipy.laboratory.registry_binding.v1"

LaboratoryProviderKind = Literal[
    "local_fake",
    "autodoc_native",
    "genai_external",
    "partner_remote",
]
LaboratoryExecutionBoundary = Literal[
    "in_process",
    "local_process",
    "remote_service",
]
LaboratoryAvailability = Literal[
    "declared",
    "disabled",
    "unavailable",
    "ready",
]
LaboratoryVisitStatus = Literal[
    "completed",
    "needs_context",
    "needs_specialist",
    "rejected",
    "failed",
    "cancelled",
]

_ALLOWED_PROVIDER_KINDS = frozenset(
    {"local_fake", "autodoc_native", "genai_external", "partner_remote"}
)
_ALLOWED_EXECUTION_BOUNDARIES = frozenset(
    {"in_process", "local_process", "remote_service"}
)
_ALLOWED_AVAILABILITY = frozenset(
    {"declared", "disabled", "unavailable", "ready"}
)
_ALLOWED_VISIT_STATUSES = frozenset(
    {
        "completed",
        "needs_context",
        "needs_specialist",
        "rejected",
        "failed",
        "cancelled",
    }
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9_.-]+$")
_COMPONENT_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")

_LABORATORY_PREFIXES = ("laboratory:",)
_VISIT_PREFIXES = ("laboratory-visit:",)
_SPECIALIST_PREFIXES = ("specialist:", "llm:")
_CONVERSATION_PREFIXES = ("laboratory-conversation:",)
_RETURN_ROUTE_PREFIXES = ("route:", "specialist-path:")
_CONTRACT_PREFIXES = ("contract:",)
_CONTEXT_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "artifact:",
)
_EVIDENCE_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "artifact:",
    "validation:",
)
_FOLLOWUP_PREFIXES = ("laboratory-followup:", "specialist-demand:")

_MAX_DURATION_MS = 86_400_000
_MAX_OUTPUT_CHARS = 1_000_000
_MAX_CONTEXT_REFS = 1_024
_MAX_EVIDENCE_REFS = 1_024
_MAX_FOLLOWUP_REQUESTS = 128
_MAX_SPECIALIST_MESSAGES = 1_024
_MAX_EXTERNAL_CALLS = 128

_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


class LaboratoryContractError(ValueError):
    """Raised when a laboratory contract is incoherent."""


@dataclass(frozen=True, slots=True)
class LaboratoryResourceBudget:
    """Explicit upper bounds for one laboratory visit."""

    schema: str = LABORATORY_RESOURCE_BUDGET_SCHEMA
    max_duration_ms: int = 60_000
    max_output_chars: int = 32_768
    max_context_refs: int = 64
    max_evidence_refs: int = 64
    max_followup_requests: int = 16
    max_specialist_messages: int = 64
    max_external_calls: int = 0
    allow_network: bool = False

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_RESOURCE_BUDGET_SCHEMA:
            raise LaboratoryContractError("unsupported laboratory resource budget schema")
        _require_int_range(
            "max_duration_ms", self.max_duration_ms, minimum=1, maximum=_MAX_DURATION_MS
        )
        _require_int_range(
            "max_output_chars",
            self.max_output_chars,
            minimum=1,
            maximum=_MAX_OUTPUT_CHARS,
        )
        _require_int_range(
            "max_context_refs",
            self.max_context_refs,
            minimum=0,
            maximum=_MAX_CONTEXT_REFS,
        )
        _require_int_range(
            "max_evidence_refs",
            self.max_evidence_refs,
            minimum=0,
            maximum=_MAX_EVIDENCE_REFS,
        )
        _require_int_range(
            "max_followup_requests",
            self.max_followup_requests,
            minimum=0,
            maximum=_MAX_FOLLOWUP_REQUESTS,
        )
        _require_int_range(
            "max_specialist_messages",
            self.max_specialist_messages,
            minimum=0,
            maximum=_MAX_SPECIALIST_MESSAGES,
        )
        _require_int_range(
            "max_external_calls",
            self.max_external_calls,
            minimum=0,
            maximum=_MAX_EXTERNAL_CALLS,
        )
        if not self.allow_network and self.max_external_calls != 0:
            raise LaboratoryContractError(
                "max_external_calls must be 0 when allow_network is false"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "max_duration_ms": self.max_duration_ms,
            "max_output_chars": self.max_output_chars,
            "max_context_refs": self.max_context_refs,
            "max_evidence_refs": self.max_evidence_refs,
            "max_followup_requests": self.max_followup_requests,
            "max_specialist_messages": self.max_specialist_messages,
            "max_external_calls": self.max_external_calls,
            "allow_network": self.allow_network,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryDescriptor:
    """One declared laboratory framework, not an instantiated provider."""

    schema: str
    laboratory_ref: str
    provider_kind: LaboratoryProviderKind
    display_name: str
    capabilities: tuple[str, ...]
    accepted_input_contract_refs: tuple[str, ...]
    produced_output_contract_refs: tuple[str, ...]
    execution_boundary: LaboratoryExecutionBoundary
    availability: LaboratoryAvailability = "declared"
    enabled: bool = False
    network_allowed: bool = False
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_DESCRIPTOR_SCHEMA:
            raise LaboratoryContractError("unsupported laboratory descriptor schema")
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        if self.provider_kind not in _ALLOWED_PROVIDER_KINDS:
            raise LaboratoryContractError("unsupported laboratory provider_kind")
        _require_non_empty("display_name", self.display_name)
        object.__setattr__(
            self,
            "capabilities",
            _normalize_capabilities(self.capabilities),
        )
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
        if self.execution_boundary not in _ALLOWED_EXECUTION_BOUNDARIES:
            raise LaboratoryContractError("unsupported laboratory execution_boundary")
        if self.availability not in _ALLOWED_AVAILABILITY:
            raise LaboratoryContractError("unsupported laboratory availability")
        if self.enabled and self.availability != "ready":
            raise LaboratoryContractError(
                "enabled laboratory descriptor must have availability ready"
            )
        if self.enabled and self.execution_boundary == "remote_service":
            if not self.network_allowed:
                raise LaboratoryContractError(
                    "enabled remote_service laboratory must allow network"
                )
        if not self.network_allowed and self.execution_boundary == "remote_service":
            if self.availability == "ready":
                raise LaboratoryContractError(
                    "ready remote_service laboratory must allow network"
                )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "laboratory_ref": self.laboratory_ref,
            "provider_kind": self.provider_kind,
            "display_name": self.display_name,
            "capabilities": list(self.capabilities),
            "accepted_input_contract_refs": list(
                self.accepted_input_contract_refs
            ),
            "produced_output_contract_refs": list(
                self.produced_output_contract_refs
            ),
            "execution_boundary": self.execution_boundary,
            "availability": self.availability,
            "enabled": self.enabled,
            "network_allowed": self.network_allowed,
            "metadata": dict(self.metadata),
            "provider_instantiated": False,
            "registry_attached": False,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryVisitRequest:
    """One bounded request for a specialist visit inside a laboratory."""

    schema: str
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    objective_ref: str
    source_candidate_ref: str
    context_generation: int
    input_contract_ref: str
    expected_output_contract_ref: str
    resource_budget: LaboratoryResourceBudget
    return_route_ref: str
    context_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    origin_laboratory_ref: str | None = None
    target_laboratory_ref: str | None = None
    conversation_ref: str | None = None
    parent_visit_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_VISIT_REQUEST_SCHEMA:
            raise LaboratoryContractError("unsupported laboratory visit request schema")
        _require_typed_ref("visit_ref", self.visit_ref, required_prefixes=_VISIT_PREFIXES)
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        _require_typed_ref("objective_ref", self.objective_ref)
        _require_typed_ref("source_candidate_ref", self.source_candidate_ref)
        _require_int_range(
            "context_generation",
            self.context_generation,
            minimum=0,
            maximum=2_147_483_647,
        )
        _require_typed_ref(
            "input_contract_ref",
            self.input_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        _require_typed_ref(
            "expected_output_contract_ref",
            self.expected_output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        if not isinstance(self.resource_budget, LaboratoryResourceBudget):
            raise LaboratoryContractError(
                "resource_budget must be a LaboratoryResourceBudget"
            )
        _require_typed_ref(
            "return_route_ref",
            self.return_route_ref,
            required_prefixes=_RETURN_ROUTE_PREFIXES,
        )
        context_refs = _normalize_refs(
            "context_refs",
            self.context_refs,
            allow_empty=True,
            required_prefixes=_CONTEXT_PREFIXES,
        )
        evidence_refs = _normalize_refs(
            "evidence_refs",
            self.evidence_refs,
            allow_empty=True,
            required_prefixes=_EVIDENCE_PREFIXES,
        )
        if len(context_refs) > self.resource_budget.max_context_refs:
            raise LaboratoryContractError(
                "context_refs exceed resource_budget.max_context_refs"
            )
        if len(evidence_refs) > self.resource_budget.max_evidence_refs:
            raise LaboratoryContractError(
                "evidence_refs exceed resource_budget.max_evidence_refs"
            )
        object.__setattr__(self, "context_refs", context_refs)
        object.__setattr__(self, "evidence_refs", evidence_refs)

        origin = self.origin_laboratory_ref or self.laboratory_ref
        target = self.target_laboratory_ref or self.laboratory_ref
        _require_typed_ref(
            "origin_laboratory_ref",
            origin,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "target_laboratory_ref",
            target,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        if target != self.laboratory_ref:
            raise LaboratoryContractError(
                "target_laboratory_ref must match laboratory_ref for this visit"
            )
        if origin != target and not self.conversation_ref:
            raise LaboratoryContractError(
                "cross-laboratory visit requires conversation_ref"
            )
        if self.conversation_ref is not None:
            _require_typed_ref(
                "conversation_ref",
                self.conversation_ref,
                required_prefixes=_CONVERSATION_PREFIXES,
            )
        if self.parent_visit_ref is not None:
            _require_typed_ref(
                "parent_visit_ref",
                self.parent_visit_ref,
                required_prefixes=_VISIT_PREFIXES,
            )
            if self.parent_visit_ref == self.visit_ref:
                raise LaboratoryContractError(
                    "parent_visit_ref must not equal visit_ref"
                )
        object.__setattr__(self, "origin_laboratory_ref", origin)
        object.__setattr__(self, "target_laboratory_ref", target)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "visit_ref": self.visit_ref,
            "laboratory_ref": self.laboratory_ref,
            "specialist_ref": self.specialist_ref,
            "objective_ref": self.objective_ref,
            "source_candidate_ref": self.source_candidate_ref,
            "context_generation": self.context_generation,
            "input_contract_ref": self.input_contract_ref,
            "expected_output_contract_ref": self.expected_output_contract_ref,
            "resource_budget": self.resource_budget.to_mapping(),
            "return_route_ref": self.return_route_ref,
            "context_refs": list(self.context_refs),
            "evidence_refs": list(self.evidence_refs),
            "origin_laboratory_ref": self.origin_laboratory_ref,
            "target_laboratory_ref": self.target_laboratory_ref,
            "conversation_ref": self.conversation_ref,
            "parent_visit_ref": self.parent_visit_ref,
            "metadata": dict(self.metadata),
            "next_boundary": "Scheduler.emit()",
            "direct_backend_access_allowed": False,
            "publication_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryVisitResult:
    """Immutable result returned by a provider membrane for one visit."""

    schema: str
    visit_ref: str
    laboratory_ref: str
    specialist_ref: str
    status: LaboratoryVisitStatus
    output_contract_ref: str
    machine_result: Mapping[str, Any]
    human_representation: str
    confidence: float
    evidence_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    requested_context_refs: tuple[str, ...] = ()
    requested_specialist_refs: tuple[str, ...] = ()
    requested_laboratory_refs: tuple[str, ...] = ()
    followup_request_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    conversation_ref: str | None = None
    parent_visit_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_VISIT_RESULT_SCHEMA:
            raise LaboratoryContractError("unsupported laboratory visit result schema")
        _require_typed_ref("visit_ref", self.visit_ref, required_prefixes=_VISIT_PREFIXES)
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        _require_typed_ref(
            "specialist_ref",
            self.specialist_ref,
            required_prefixes=_SPECIALIST_PREFIXES,
        )
        if self.status not in _ALLOWED_VISIT_STATUSES:
            raise LaboratoryContractError("unsupported laboratory visit status")
        _require_typed_ref(
            "output_contract_ref",
            self.output_contract_ref,
            required_prefixes=_CONTRACT_PREFIXES,
        )
        if not isinstance(self.machine_result, Mapping):
            raise LaboratoryContractError("machine_result must be a mapping")
        frozen_result = _freeze_json_mapping(self.machine_result)
        if self.status == "completed" and not frozen_result:
            raise LaboratoryContractError(
                "completed laboratory visit requires a machine_result"
            )
        object.__setattr__(self, "machine_result", frozen_result)
        _require_non_empty("human_representation", self.human_representation)
        if not 0.0 <= self.confidence <= 1.0:
            raise LaboratoryContractError(
                "confidence must be between 0.0 and 1.0"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                allow_empty=True,
                required_prefixes=_EVIDENCE_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "assumptions",
            _normalize_texts("assumptions", self.assumptions, allow_empty=True),
        )
        object.__setattr__(
            self,
            "requested_context_refs",
            _normalize_refs(
                "requested_context_refs",
                self.requested_context_refs,
                allow_empty=True,
                required_prefixes=_CONTEXT_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "requested_specialist_refs",
            _normalize_refs(
                "requested_specialist_refs",
                self.requested_specialist_refs,
                allow_empty=True,
                required_prefixes=_SPECIALIST_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "requested_laboratory_refs",
            _normalize_refs(
                "requested_laboratory_refs",
                self.requested_laboratory_refs,
                allow_empty=True,
                required_prefixes=_LABORATORY_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "followup_request_refs",
            _normalize_refs(
                "followup_request_refs",
                self.followup_request_refs,
                allow_empty=True,
                required_prefixes=_FOLLOWUP_PREFIXES,
            ),
        )
        object.__setattr__(
            self,
            "provenance_refs",
            _normalize_refs(
                "provenance_refs",
                self.provenance_refs,
                allow_empty=True,
            ),
        )
        if self.conversation_ref is not None:
            _require_typed_ref(
                "conversation_ref",
                self.conversation_ref,
                required_prefixes=_CONVERSATION_PREFIXES,
            )
        if self.parent_visit_ref is not None:
            _require_typed_ref(
                "parent_visit_ref",
                self.parent_visit_ref,
                required_prefixes=_VISIT_PREFIXES,
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "visit_ref": self.visit_ref,
            "laboratory_ref": self.laboratory_ref,
            "specialist_ref": self.specialist_ref,
            "status": self.status,
            "output_contract_ref": self.output_contract_ref,
            "machine_result": _thaw_json(self.machine_result),
            "human_representation": self.human_representation,
            "confidence": self.confidence,
            "evidence_refs": list(self.evidence_refs),
            "assumptions": list(self.assumptions),
            "requested_context_refs": list(self.requested_context_refs),
            "requested_specialist_refs": list(self.requested_specialist_refs),
            "requested_laboratory_refs": list(self.requested_laboratory_refs),
            "followup_request_refs": list(self.followup_request_refs),
            "provenance_refs": list(self.provenance_refs),
            "conversation_ref": self.conversation_ref,
            "parent_visit_ref": self.parent_visit_ref,
            "publication_allowed": False,
            "eventbus_command_allowed": False,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryRegistryBindingPlan:
    """Declarative plan targeting the existing 0257 registry record."""

    schema: str
    laboratory_ref: str
    component_id: str
    capabilities: tuple[str, ...]
    target_registry_module: str = (
        "context.scheduler_owned_runtime_registry_0257"
    )
    target_registration_type: str = (
        "SchedulerOwnedRuntimeComponentRegistration"
    )
    owner: str = "scheduler"
    role: str = "command"
    provider_source_paths: tuple[str, ...] = ()
    ready_for_registry_attachment: bool = False
    provider_active: bool = False
    creates_parallel_registry: bool = False
    creates_runtime_manager: bool = False
    creates_scheduler: bool = False
    creates_eventbus: bool = False
    modifies_scheduler_run: bool = False

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_REGISTRY_BINDING_SCHEMA:
            raise LaboratoryContractError(
                "unsupported laboratory registry binding schema"
            )
        _require_typed_ref(
            "laboratory_ref",
            self.laboratory_ref,
            required_prefixes=_LABORATORY_PREFIXES,
        )
        if not _COMPONENT_ID_RE.match(self.component_id):
            raise LaboratoryContractError(
                "component_id must use lowercase snake_case"
            )
        object.__setattr__(
            self,
            "capabilities",
            _normalize_capabilities(self.capabilities),
        )
        _require_non_empty("target_registry_module", self.target_registry_module)
        _require_non_empty(
            "target_registration_type", self.target_registration_type
        )
        if self.owner != "scheduler":
            raise LaboratoryContractError("registry binding owner must be scheduler")
        if self.role != "command":
            raise LaboratoryContractError("laboratory registry role must be command")
        paths = tuple(
            path.strip()
            for path in self.provider_source_paths
            if isinstance(path, str) and path.strip()
        )
        if len(paths) != len(self.provider_source_paths):
            raise LaboratoryContractError(
                "provider_source_paths must not contain empty values"
            )
        object.__setattr__(self, "provider_source_paths", tuple(dict.fromkeys(paths)))
        forbidden_flags = (
            self.creates_parallel_registry,
            self.creates_runtime_manager,
            self.creates_scheduler,
            self.creates_eventbus,
            self.modifies_scheduler_run,
        )
        if any(forbidden_flags):
            raise LaboratoryContractError(
                "laboratory binding must not create parallel authorities"
            )
        if self.ready_for_registry_attachment:
            if not self.provider_active or not self.provider_source_paths:
                raise LaboratoryContractError(
                    "ready registry binding requires an active provider source"
                )
        if self.provider_active and not self.provider_source_paths:
            raise LaboratoryContractError(
                "active provider requires provider_source_paths"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "laboratory_ref": self.laboratory_ref,
            "component_id": self.component_id,
            "capabilities": list(self.capabilities),
            "target_registry_module": self.target_registry_module,
            "target_registration_type": self.target_registration_type,
            "owner": self.owner,
            "role": self.role,
            "provider_source_paths": list(self.provider_source_paths),
            "ready_for_registry_attachment": self.ready_for_registry_attachment,
            "provider_active": self.provider_active,
            "creates_parallel_registry": self.creates_parallel_registry,
            "creates_runtime_manager": self.creates_runtime_manager,
            "creates_scheduler": self.creates_scheduler,
            "creates_eventbus": self.creates_eventbus,
            "modifies_scheduler_run": self.modifies_scheduler_run,
        }


def build_laboratory_registry_binding_plan(
    descriptor: LaboratoryDescriptor,
) -> LaboratoryRegistryBindingPlan:
    """Build an inactive binding plan for the existing Scheduler-owned registry."""

    component_suffix = re.sub(
        r"[^a-z0-9_]+",
        "_",
        descriptor.laboratory_ref.removeprefix("laboratory:").lower(),
    ).strip("_")
    if not component_suffix:
        raise LaboratoryContractError(
            "laboratory_ref must produce a non-empty component suffix"
        )
    return LaboratoryRegistryBindingPlan(
        schema=LABORATORY_REGISTRY_BINDING_SCHEMA,
        laboratory_ref=descriptor.laboratory_ref,
        component_id=f"laboratory_provider_{component_suffix}",
        capabilities=descriptor.capabilities,
    )


def validate_laboratory_visit_result(
    request: LaboratoryVisitRequest,
    result: LaboratoryVisitResult,
) -> tuple[str, ...]:
    """Validate a provider result against its bounded request."""

    issues: list[str] = []
    if result.visit_ref != request.visit_ref:
        issues.append("result visit_ref must match request")
    if result.laboratory_ref != request.laboratory_ref:
        issues.append("result laboratory_ref must match request")
    if result.specialist_ref != request.specialist_ref:
        issues.append("result specialist_ref must match request")
    if result.output_contract_ref != request.expected_output_contract_ref:
        issues.append("result output_contract_ref must match request")
    if result.conversation_ref != request.conversation_ref:
        issues.append("result conversation_ref must match request")
    if result.parent_visit_ref != request.parent_visit_ref:
        issues.append("result parent_visit_ref must match request")
    if len(result.human_representation) > request.resource_budget.max_output_chars:
        issues.append("result human_representation exceeds max_output_chars")
    if len(result.evidence_refs) > request.resource_budget.max_evidence_refs:
        issues.append("result evidence_refs exceed max_evidence_refs")
    if len(result.requested_context_refs) > request.resource_budget.max_context_refs:
        issues.append("result requested_context_refs exceed max_context_refs")
    followup_count = (
        len(result.requested_specialist_refs)
        + len(result.requested_laboratory_refs)
        + len(result.followup_request_refs)
    )
    if followup_count > request.resource_budget.max_followup_requests:
        issues.append("result follow-up requests exceed max_followup_requests")
    if result.requested_laboratory_refs and not request.resource_budget.allow_network:
        external_laboratories = tuple(
            ref
            for ref in result.requested_laboratory_refs
            if ref != request.laboratory_ref
        )
        if external_laboratories:
            issues.append(
                "external laboratory request requires a network-enabled budget"
            )
    return tuple(issues)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LaboratoryContractError(f"{name} must be non-empty")


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefixes: tuple[str, ...] | None = None,
) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise LaboratoryContractError(f"{name} must be a typed reference")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise LaboratoryContractError(
            f"{name} must start with one of: {', '.join(required_prefixes)}"
        )


def _require_int_range(
    name: str,
    value: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LaboratoryContractError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise LaboratoryContractError(
            f"{name} must be between {minimum} and {maximum}"
        )


def _normalize_capabilities(values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    )
    if not normalized:
        raise LaboratoryContractError("capabilities must not be empty")
    unique = tuple(dict.fromkeys(normalized))
    for capability in unique:
        if not _CAPABILITY_RE.match(capability):
            raise LaboratoryContractError(
                f"invalid laboratory capability: {capability}"
            )
    return unique


def _normalize_refs(
    name: str,
    refs: Sequence[str],
    *,
    allow_empty: bool = False,
    required_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    values = tuple(refs)
    if not values and not allow_empty:
        raise LaboratoryContractError(f"{name} must not be empty")
    for ref in values:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return tuple(dict.fromkeys(values))


def _normalize_texts(
    name: str,
    values: Sequence[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    normalized = tuple(
        value.strip()
        for value in values
        if isinstance(value, str) and value.strip()
    )
    if not normalized and not allow_empty:
        raise LaboratoryContractError(f"{name} must not be empty")
    return tuple(dict.fromkeys(normalized))


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(dict(normalized).items())


def _freeze_json_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen: dict[str, Any] = {}
    for key, value in values.items():
        _require_non_empty("machine_result key", key)
        frozen[key] = _freeze_json(value)
    return MappingProxyType(frozen)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise LaboratoryContractError(
        f"machine_result contains non-JSON value: {type(value).__name__}"
    )


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = (
    "LABORATORY_DESCRIPTOR_SCHEMA",
    "LABORATORY_FRAMEWORK_CONTRACT_VERSION",
    "LABORATORY_REGISTRY_BINDING_SCHEMA",
    "LABORATORY_RESOURCE_BUDGET_SCHEMA",
    "LABORATORY_VISIT_REQUEST_SCHEMA",
    "LABORATORY_VISIT_RESULT_SCHEMA",
    "LaboratoryAvailability",
    "LaboratoryContractError",
    "LaboratoryDescriptor",
    "LaboratoryExecutionBoundary",
    "LaboratoryProviderKind",
    "LaboratoryRegistryBindingPlan",
    "LaboratoryResourceBudget",
    "LaboratoryVisitRequest",
    "LaboratoryVisitResult",
    "LaboratoryVisitStatus",
    "build_laboratory_registry_binding_plan",
    "validate_laboratory_visit_result",
)
