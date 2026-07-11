"""Deterministic local fake laboratory provider for phase 0273-r3.

This module implements one bounded provider membrane for
``missipy.laboratory.v1``.  It is a tracer bullet used to validate the
laboratory boundary before integrating the native Autodoc laboratory, GenAI,
or a partner framework.

The provider is local, synchronous, deterministic, stdlib-only and network
closed.  It does not own orchestration, persistence, vector recall, GitHub
mutation, event publication, route runtime, supervision or rendering.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Protocol, runtime_checkable

from context.laboratory_framework_contract_0273 import (
    LABORATORY_DESCRIPTOR_SCHEMA,
    LABORATORY_REGISTRY_BINDING_SCHEMA,
    LABORATORY_VISIT_RESULT_SCHEMA,
    LaboratoryContractError,
    LaboratoryDescriptor,
    LaboratoryRegistryBindingPlan,
    LaboratoryVisitRequest,
    LaboratoryVisitResult,
    validate_laboratory_visit_result,
)
from context.scheduler_owned_runtime_registry_0257 import (
    SchedulerOwnedRuntimeComponentRegistration,
    SchedulerOwnedRuntimeRegistry,
    validate_scheduler_owned_runtime_registry,
)

DETERMINISTIC_FAKE_LABORATORY_PROVIDER_VERSION = "0273.r3"
DETERMINISTIC_FAKE_LABORATORY_REF = "laboratory:local-fake"
DETERMINISTIC_FAKE_COMPONENT_ID = "laboratory_provider_local_fake"
DETERMINISTIC_FAKE_PROVIDER_SCHEMA = "missipy.laboratory.provider.fake.v1"
DETERMINISTIC_FAKE_EXECUTION_SCHEMA = "missipy.laboratory.execution.fake.v1"
DETERMINISTIC_FAKE_SOURCE_PATHS = (
    "src/context/deterministic_fake_laboratory_provider_0273.py",
    "src/context/laboratory_framework_contract_0273.py",
)

_ALLOWED_SCENARIOS = frozenset(
    {
        "completed",
        "needs_context",
        "needs_specialist",
        "rejected",
        "failed",
    }
)


class LaboratoryProviderExecutionError(RuntimeError):
    """Raised when a provider cannot execute a valid bounded visit."""


@runtime_checkable
class LaboratoryProvider(Protocol):
    """Minimal provider membrane used at the existing Handler boundary."""

    @property
    def descriptor(self) -> LaboratoryDescriptor:
        """Return the immutable provider descriptor."""

    def execute(self, request: LaboratoryVisitRequest) -> LaboratoryVisitResult:
        """Execute one bounded visit without owning orchestration."""


@dataclass(frozen=True, slots=True)
class DeterministicFakeLaboratoryProvider:
    """Local deterministic fake implementing one laboratory visit."""

    descriptor: LaboratoryDescriptor
    provider_schema: str = DETERMINISTIC_FAKE_PROVIDER_SCHEMA

    def __post_init__(self) -> None:
        if self.provider_schema != DETERMINISTIC_FAKE_PROVIDER_SCHEMA:
            raise LaboratoryContractError("unsupported fake laboratory provider schema")
        if self.descriptor.laboratory_ref != DETERMINISTIC_FAKE_LABORATORY_REF:
            raise LaboratoryContractError(
                "fake provider requires laboratory:local-fake descriptor"
            )
        if self.descriptor.provider_kind != "local_fake":
            raise LaboratoryContractError("fake provider requires provider_kind local_fake")
        if self.descriptor.execution_boundary != "in_process":
            raise LaboratoryContractError("fake provider must execute in_process")
        if self.descriptor.availability != "ready" or not self.descriptor.enabled:
            raise LaboratoryContractError("fake provider descriptor must be enabled and ready")
        if self.descriptor.network_allowed:
            raise LaboratoryContractError("fake provider must remain network closed")

    def execute(self, request: LaboratoryVisitRequest) -> LaboratoryVisitResult:
        _validate_request_for_provider(self.descriptor, request)
        scenario = _request_scenario(request)
        digest = _request_digest(request)
        result = _build_result(request=request, scenario=scenario, digest=digest)
        issues = validate_laboratory_visit_result(request, result)
        if issues:
            raise LaboratoryProviderExecutionError("; ".join(issues))
        return result


@dataclass(frozen=True, slots=True)
class FakeLaboratoryExecutionRecord:
    """Serializable handler-side record for one fake provider call."""

    schema: str
    provider_ref: str
    registration_component_id: str
    request: LaboratoryVisitRequest
    result: LaboratoryVisitResult
    result_valid: bool
    validation_issues: tuple[str, ...]
    handler_boundary: str = "Dispatcher -> Handler -> LaboratoryProvider.execute"
    scheduler_path_required: bool = True
    provider_owns_orchestration: bool = False
    provider_owns_persistence: bool = False
    provider_owns_vector_index: bool = False
    provider_publishes_commands: bool = False
    provider_uses_network: bool = False
    real_backend_used: bool = False

    def __post_init__(self) -> None:
        if self.schema != DETERMINISTIC_FAKE_EXECUTION_SCHEMA:
            raise LaboratoryContractError("unsupported fake execution record schema")
        if self.provider_ref != self.request.laboratory_ref:
            raise LaboratoryContractError("provider_ref must match request laboratory_ref")
        if self.result.visit_ref != self.request.visit_ref:
            raise LaboratoryContractError("result must belong to request visit_ref")
        if self.result_valid != (not self.validation_issues):
            raise LaboratoryContractError("result_valid must reflect validation_issues")
        if not self.scheduler_path_required:
            raise LaboratoryContractError("Scheduler path must remain required")
        forbidden = (
            self.provider_owns_orchestration,
            self.provider_owns_persistence,
            self.provider_owns_vector_index,
            self.provider_publishes_commands,
            self.provider_uses_network,
            self.real_backend_used,
        )
        if any(forbidden):
            raise LaboratoryContractError("fake execution must not claim external ownership")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "provider_ref": self.provider_ref,
            "registration_component_id": self.registration_component_id,
            "request": self.request.to_mapping(),
            "result": self.result.to_mapping(),
            "result_valid": self.result_valid,
            "validation_issues": list(self.validation_issues),
            "handler_boundary": self.handler_boundary,
            "scheduler_path_required": self.scheduler_path_required,
            "provider_owns_orchestration": self.provider_owns_orchestration,
            "provider_owns_persistence": self.provider_owns_persistence,
            "provider_owns_vector_index": self.provider_owns_vector_index,
            "provider_publishes_commands": self.provider_publishes_commands,
            "provider_uses_network": self.provider_uses_network,
            "real_backend_used": self.real_backend_used,
        }


def build_deterministic_fake_laboratory_descriptor() -> LaboratoryDescriptor:
    """Build the single enabled descriptor used by the r3 tracer bullet."""

    return LaboratoryDescriptor(
        schema=LABORATORY_DESCRIPTOR_SCHEMA,
        laboratory_ref=DETERMINISTIC_FAKE_LABORATORY_REF,
        provider_kind="local_fake",
        display_name="Autodoc deterministic fake laboratory",
        capabilities=(
            "laboratory.visit.execute",
            "laboratory.specialist.simulate",
            "laboratory.followup.request",
        ),
        accepted_input_contract_refs=(
            "contract:missipy.specialist.demand.v1",
            "contract:missipy.laboratory.visit_request.v1",
        ),
        produced_output_contract_refs=(
            "contract:missipy.laboratory.visit_result.v1",
        ),
        execution_boundary="in_process",
        availability="ready",
        enabled=True,
        network_allowed=False,
        metadata=(
            ("implementation", "deterministic_fake"),
            ("backend_status", "tracer_bullet"),
        ),
    )


def build_deterministic_fake_laboratory_provider() -> DeterministicFakeLaboratoryProvider:
    return DeterministicFakeLaboratoryProvider(
        descriptor=build_deterministic_fake_laboratory_descriptor()
    )


def build_deterministic_fake_laboratory_binding_plan() -> LaboratoryRegistryBindingPlan:
    """Build the active r3 plan targeting the existing 0257 registry type."""

    descriptor = build_deterministic_fake_laboratory_descriptor()
    return LaboratoryRegistryBindingPlan(
        schema=LABORATORY_REGISTRY_BINDING_SCHEMA,
        laboratory_ref=descriptor.laboratory_ref,
        component_id=DETERMINISTIC_FAKE_COMPONENT_ID,
        capabilities=descriptor.capabilities,
        provider_source_paths=DETERMINISTIC_FAKE_SOURCE_PATHS,
        ready_for_registry_attachment=True,
        provider_active=True,
    )


def build_deterministic_fake_laboratory_registration() -> SchedulerOwnedRuntimeComponentRegistration:
    """Convert the validated plan to the existing registry registration type."""

    plan = build_deterministic_fake_laboratory_binding_plan()
    return SchedulerOwnedRuntimeComponentRegistration(
        component_id=plan.component_id,
        surface="laboratory_provider",
        owner=plan.owner,
        role=plan.role,
        capabilities=plan.capabilities,
        depends_on=(),
        source_paths=plan.provider_source_paths,
        runtime_api_kind="scheduler_owned_object",
        selected_from_existing_surfaces=False,
    )


def bind_deterministic_fake_laboratory_registration(
    registry: SchedulerOwnedRuntimeRegistry,
) -> SchedulerOwnedRuntimeRegistry:
    """Return the existing registry value with the fake registration appended.

    Exact replay is idempotent.  A conflicting registration with the same
    component id is rejected.  No registry object is mutated in place.
    """

    registration = build_deterministic_fake_laboratory_registration()
    by_id = {item.component_id: item for item in registry.registrations}
    existing = by_id.get(registration.component_id)
    if existing is not None:
        if existing == registration:
            return registry
        raise LaboratoryContractError(
            "conflicting laboratory provider registration already exists"
        )
    updated = SchedulerOwnedRuntimeRegistry(
        registrations=registry.registrations + (registration,),
        source_map_complete=registry.source_map_complete,
        owner=registry.owner,
        launcher_bootstrap_only=registry.launcher_bootstrap_only,
        eventbus_observation_only=registry.eventbus_observation_only,
        no_cli_per_component=registry.no_cli_per_component,
        creates_runtime_manager=registry.creates_runtime_manager,
        instantiates_components=registry.instantiates_components,
    )
    issues = validate_scheduler_owned_runtime_registry(updated)
    if issues:
        raise LaboratoryContractError("; ".join(issues))
    return updated


def execute_deterministic_fake_laboratory_visit(
    request: LaboratoryVisitRequest,
    *,
    provider: LaboratoryProvider | None = None,
) -> FakeLaboratoryExecutionRecord:
    """Handler-side membrane for one deterministic fake visit."""

    selected = provider or build_deterministic_fake_laboratory_provider()
    result = selected.execute(request)
    issues = validate_laboratory_visit_result(request, result)
    return FakeLaboratoryExecutionRecord(
        schema=DETERMINISTIC_FAKE_EXECUTION_SCHEMA,
        provider_ref=selected.descriptor.laboratory_ref,
        registration_component_id=DETERMINISTIC_FAKE_COMPONENT_ID,
        request=request,
        result=result,
        result_valid=not issues,
        validation_issues=issues,
    )


def _validate_request_for_provider(
    descriptor: LaboratoryDescriptor,
    request: LaboratoryVisitRequest,
) -> None:
    if request.laboratory_ref != descriptor.laboratory_ref:
        raise LaboratoryProviderExecutionError(
            "request laboratory_ref does not match provider descriptor"
        )
    if request.target_laboratory_ref != descriptor.laboratory_ref:
        raise LaboratoryProviderExecutionError(
            "request target_laboratory_ref does not match provider descriptor"
        )
    if request.input_contract_ref not in descriptor.accepted_input_contract_refs:
        raise LaboratoryProviderExecutionError(
            "request input contract is not accepted by provider"
        )
    if request.expected_output_contract_ref not in descriptor.produced_output_contract_refs:
        raise LaboratoryProviderExecutionError(
            "request output contract is not produced by provider"
        )
    if request.resource_budget.allow_network:
        raise LaboratoryProviderExecutionError(
            "deterministic fake provider refuses network-enabled visits"
        )
    if request.resource_budget.max_external_calls != 0:
        raise LaboratoryProviderExecutionError(
            "deterministic fake provider refuses external calls"
        )


def _request_scenario(request: LaboratoryVisitRequest) -> str:
    metadata = dict(request.metadata)
    scenario = metadata.get("fake_scenario", "completed")
    if scenario not in _ALLOWED_SCENARIOS:
        raise LaboratoryProviderExecutionError(
            f"unsupported deterministic fake scenario: {scenario}"
        )
    return scenario


def _request_digest(request: LaboratoryVisitRequest) -> str:
    encoded = json.dumps(
        request.to_mapping(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _build_result(
    *,
    request: LaboratoryVisitRequest,
    scenario: str,
    digest: str,
) -> LaboratoryVisitResult:
    short_digest = digest.split(":", 1)[1][:16]
    common_machine_result: dict[str, object] = {
        "schema": DETERMINISTIC_FAKE_EXECUTION_SCHEMA,
        "provider_kind": "local_fake",
        "scenario": scenario,
        "request_digest": digest,
        "objective_ref": request.objective_ref,
        "context_generation": request.context_generation,
        "context_ref_count": len(request.context_refs),
        "evidence_ref_count": len(request.evidence_refs),
        "deterministic": True,
        "real_backend_used": False,
    }
    kwargs: dict[str, object] = {}
    if scenario == "completed":
        human = f"Deterministic fake laboratory completed visit {request.visit_ref}."
        common_machine_result["finding"] = "bounded_fake_visit_completed"
        status = "completed"
        confidence = 0.5
    elif scenario == "needs_context":
        human = f"Deterministic fake laboratory requests additional context for {request.visit_ref}."
        common_machine_result["finding"] = "additional_context_required"
        kwargs["requested_context_refs"] = (f"ctx:requested:{short_digest}",)
        kwargs["followup_request_refs"] = (
            f"laboratory-followup:context:{short_digest}",
        )
        status = "needs_context"
        confidence = 0.25
    elif scenario == "needs_specialist":
        human = f"Deterministic fake laboratory requests a validator for {request.visit_ref}."
        common_machine_result["finding"] = "peer_validation_required"
        kwargs["requested_specialist_refs"] = ("specialist:validator",)
        kwargs["followup_request_refs"] = (
            f"laboratory-followup:specialist:{short_digest}",
        )
        status = "needs_specialist"
        confidence = 0.25
    elif scenario == "rejected":
        human = f"Deterministic fake laboratory rejected visit {request.visit_ref}."
        common_machine_result["finding"] = "fake_policy_rejection"
        status = "rejected"
        confidence = 0.0
    else:
        human = f"Deterministic fake laboratory failed visit {request.visit_ref}."
        common_machine_result["finding"] = "fake_execution_failure"
        status = "failed"
        confidence = 0.0

    return LaboratoryVisitResult(
        schema=LABORATORY_VISIT_RESULT_SCHEMA,
        visit_ref=request.visit_ref,
        laboratory_ref=request.laboratory_ref,
        specialist_ref=request.specialist_ref,
        status=status,
        output_contract_ref=request.expected_output_contract_ref,
        machine_result=common_machine_result,
        human_representation=human,
        confidence=confidence,
        evidence_refs=request.evidence_refs,
        conversation_ref=request.conversation_ref,
        parent_visit_ref=request.parent_visit_ref,
        provenance_refs=(
            request.source_candidate_ref,
            request.objective_ref,
            digest,
        ),
        **kwargs,
    )


__all__ = (
    "DETERMINISTIC_FAKE_COMPONENT_ID",
    "DETERMINISTIC_FAKE_EXECUTION_SCHEMA",
    "DETERMINISTIC_FAKE_LABORATORY_PROVIDER_VERSION",
    "DETERMINISTIC_FAKE_LABORATORY_REF",
    "DETERMINISTIC_FAKE_PROVIDER_SCHEMA",
    "DETERMINISTIC_FAKE_SOURCE_PATHS",
    "DeterministicFakeLaboratoryProvider",
    "FakeLaboratoryExecutionRecord",
    "LaboratoryProvider",
    "LaboratoryProviderExecutionError",
    "bind_deterministic_fake_laboratory_registration",
    "build_deterministic_fake_laboratory_binding_plan",
    "build_deterministic_fake_laboratory_descriptor",
    "build_deterministic_fake_laboratory_provider",
    "build_deterministic_fake_laboratory_registration",
    "execute_deterministic_fake_laboratory_visit",
)
