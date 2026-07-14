from dataclasses import FrozenInstanceError

import pytest

from context.portable_specialist_contract_0284 import (
    PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_EXECUTION_PROFILE_SCHEMA,
    SPECIALIST_LABORATORY_BINDING_SCHEMA,
    PortableSpecialistContractError,
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionProfile,
    SpecialistLaboratoryBinding,
    validate_portable_specialist_visit_contract,
)


def _capability() -> SpecialistCapabilityContract:
    return SpecialistCapabilityContract(
        schema=SPECIALIST_CAPABILITY_SCHEMA,
        capability="analysis.requirements",
        description="Extract and compare explicit engineering requirements.",
        accepted_input_contract_refs=("contract:research-request.v1",),
        produced_output_contract_refs=("contract:specialist-opinion.v1",),
        metadata=(("domain", "general"),),
    )


def _profile() -> SpecialistExecutionProfile:
    return SpecialistExecutionProfile(
        schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
        preferred_execution_boundaries=("in_process", "local_process"),
        determinism_preference="required",
        max_parallel_visits=2,
    )


def _binding(
    laboratory_ref: str,
    *,
    priority: int,
    visit_modes: tuple[str, ...] = ("visitor",),
) -> SpecialistLaboratoryBinding:
    return SpecialistLaboratoryBinding(
        schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
        specialist_ref="specialist:requirements-analyst",
        laboratory_ref=laboratory_ref,
        visit_modes=visit_modes,
        required_laboratory_capabilities=("specialist.execution",),
        priority=priority,
    )


def _descriptor() -> PortableSpecialistDescriptor:
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref="specialist:requirements-analyst",
        display_name="Requirements analyst",
        specialist_version="1.0.0",
        capabilities=(_capability(),),
        accepted_input_contract_refs=("contract:research-request.v1",),
        produced_output_contract_refs=("contract:specialist-opinion.v1",),
        execution_profile=_profile(),
        laboratory_bindings=(
            _binding("laboratory:partner-b", priority=200, visit_modes=("visitor", "transfer")),
            _binding("laboratory:local-fake", priority=10, visit_modes=("resident", "visitor")),
        ),
        availability="ready",
        metadata=(("owner", "scheduler"),),
    )


def test_descriptor_preserves_one_identity_across_laboratories() -> None:
    descriptor = _descriptor()

    assert descriptor.specialist_ref == "specialist:requirements-analyst"
    assert tuple(item.laboratory_ref for item in descriptor.laboratory_bindings) == (
        "laboratory:local-fake",
        "laboratory:partner-b",
    )
    mapping = descriptor.to_mapping()
    assert mapping["stable_identity_portable"] is True
    assert mapping["provider_instantiated"] is False
    assert mapping["runtime_attached"] is False
    assert mapping["scheduler_remains_orchestrator"] is True
    assert mapping["eventbus_observation_only"] is True
    assert mapping["sql_remains_authority"] is True
    assert mapping["qdrant_projection_recall_only"] is True


def test_contracts_are_immutable_and_serializable() -> None:
    descriptor = _descriptor()

    with pytest.raises(FrozenInstanceError):
        descriptor.display_name = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        descriptor.laboratory_bindings[0].priority = 999  # type: ignore[misc]

    mapping = descriptor.to_mapping()
    assert mapping["schema"] == PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA
    assert mapping["capabilities"][0]["capability"] == "analysis.requirements"
    assert mapping["execution_profile"]["provider_instantiated"] is False
    assert mapping["laboratory_bindings"][0]["provider_bound"] is False


def test_visit_contract_bridge_accepts_existing_route_and_visit_refs() -> None:
    descriptor = _descriptor()

    assert validate_portable_specialist_visit_contract(
        descriptor,
        specialist_ref="specialist:requirements-analyst",
        laboratory_ref="laboratory:local-fake",
        input_contract_ref="contract:research-request.v1",
        output_contract_ref="contract:specialist-opinion.v1",
        visit_mode="visitor",
    ) == ()


def test_visit_contract_bridge_reports_incompatible_route_or_laboratory() -> None:
    issues = validate_portable_specialist_visit_contract(
        _descriptor(),
        specialist_ref="specialist:other",
        laboratory_ref="laboratory:unknown",
        input_contract_ref="contract:other-input.v1",
        output_contract_ref="contract:other-output.v1",
        visit_mode="transfer",
    )

    assert issues == (
        "specialist_ref must match portable descriptor",
        "input_contract_ref is not accepted by specialist",
        "output_contract_ref is not produced by specialist",
        "laboratory_ref is not declared for specialist",
    )


def test_descriptor_rejects_binding_for_another_specialist() -> None:
    foreign = SpecialistLaboratoryBinding(
        schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
        specialist_ref="specialist:other",
        laboratory_ref="laboratory:local-fake",
        visit_modes=("visitor",),
        required_laboratory_capabilities=("specialist.execution",),
    )

    with pytest.raises(
        PortableSpecialistContractError,
        match="binding specialist_ref must match descriptor",
    ):
        PortableSpecialistDescriptor(
            schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
            specialist_ref="specialist:requirements-analyst",
            display_name="Requirements analyst",
            specialist_version="1.0.0",
            capabilities=(_capability(),),
            accepted_input_contract_refs=("contract:research-request.v1",),
            produced_output_contract_refs=("contract:specialist-opinion.v1",),
            execution_profile=_profile(),
            laboratory_bindings=(foreign,),
        )


def test_capability_contracts_must_be_declared_by_descriptor() -> None:
    with pytest.raises(
        PortableSpecialistContractError,
        match="capability input contracts must be declared",
    ):
        PortableSpecialistDescriptor(
            schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
            specialist_ref="specialist:requirements-analyst",
            display_name="Requirements analyst",
            specialist_version="1.0.0",
            capabilities=(_capability(),),
            accepted_input_contract_refs=("contract:other-input.v1",),
            produced_output_contract_refs=("contract:specialist-opinion.v1",),
            execution_profile=_profile(),
            laboratory_bindings=(_binding("laboratory:local-fake", priority=10),),
        )


def test_remote_preference_requires_explicit_network_boundary() -> None:
    with pytest.raises(
        PortableSpecialistContractError,
        match="remote_service preference requires network_allowed",
    ):
        SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("remote_service",),
            network_allowed=False,
        )


def test_accelerator_requirement_needs_a_declared_device_ref() -> None:
    with pytest.raises(
        PortableSpecialistContractError,
        match="accelerator_required needs",
    ):
        SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("local_process",),
            accelerator_required=True,
        )


def test_binding_cannot_be_constructed_as_runtime_attached() -> None:
    with pytest.raises(TypeError):
        SpecialistLaboratoryBinding(
            schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
            specialist_ref="specialist:requirements-analyst",
            laboratory_ref="laboratory:local-fake",
            visit_modes=("visitor",),
            required_laboratory_capabilities=("specialist.execution",),
            runtime_attached=True,  # type: ignore[call-arg]
        )


def test_descriptor_bridges_existing_dispatch_and_laboratory_visit_contracts() -> None:
    from context.laboratory_framework_contract_0273 import (
        LABORATORY_RESOURCE_BUDGET_SCHEMA,
        LABORATORY_VISIT_REQUEST_SCHEMA,
        LaboratoryResourceBudget,
        LaboratoryVisitRequest,
    )
    from context.scheduler_deliberation_route_contract import (
        SpecialistDispatchCommand,
    )

    dispatch = SpecialistDispatchCommand(
        command_ref="scheduler-command:specialist-dispatch-1",
        round_command_ref="scheduler-command:deliberation-round-1",
        specialist_ref="specialist:requirements-analyst",
        demand_route_ref="route:deliberation/cycle-1/round-1/demand",
        expected_opinion_route_ref="route:deliberation/cycle-1/round-1/opinion",
        bus_topic_ref="specialist-path:requirements-analyst",
    )
    visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref="laboratory-visit:requirements-1",
        laboratory_ref="laboratory:local-fake",
        specialist_ref=dispatch.specialist_ref,
        objective_ref="objective:requirements-1",
        source_candidate_ref="source-candidate:requirements-1",
        context_generation=1,
        input_contract_ref="contract:research-request.v1",
        expected_output_contract_ref="contract:specialist-opinion.v1",
        resource_budget=LaboratoryResourceBudget(
            schema=LABORATORY_RESOURCE_BUDGET_SCHEMA,
        ),
        return_route_ref=dispatch.expected_opinion_route_ref,
        context_refs=("sql:context-1",),
    )

    assert validate_portable_specialist_visit_contract(
        _descriptor(),
        specialist_ref=dispatch.specialist_ref,
        laboratory_ref=visit.laboratory_ref,
        input_contract_ref=visit.input_contract_ref,
        output_contract_ref=visit.expected_output_contract_ref,
        visit_mode="visitor",
    ) == ()
