from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from context.portable_specialist_contract_0284 import (
    PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_EXECUTION_PROFILE_SCHEMA,
    SPECIALIST_LABORATORY_BINDING_SCHEMA,
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionProfile,
    SpecialistLaboratoryBinding,
)
from context.specialist_laboratory_message_contract_0284 import (
    SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
    SpecialistLaboratoryConversation,
    SpecialistLaboratoryMessageContractError,
    build_specialist_demand_message,
    build_specialist_opinion_message,
    validate_specialist_laboratory_conversation,
)


@dataclass(frozen=True)
class VisitRequest:
    visit_ref: str = "laboratory-visit:test-001"
    laboratory_ref: str = "laboratory:local-fake"
    specialist_ref: str = "specialist:requirements-analyst"
    input_contract_ref: str = "contract:specialist-demand.v1"
    expected_output_contract_ref: str = "contract:specialist-opinion.v1"
    return_route_ref: str = "route:deliberation/test/opinion"
    context_refs: tuple[str, ...] = ("sql:context-001",)
    evidence_refs: tuple[str, ...] = ("artifact:request-001",)
    origin_laboratory_ref: str | None = None
    target_laboratory_ref: str | None = None
    conversation_ref: str | None = None


@dataclass(frozen=True)
class DemandFrame:
    frame_ref: str = "route-frame:demand-test-001"
    route_ref: str = "route:deliberation/test/demand"
    specialist_ref: str = "specialist:requirements-analyst"
    request_text: str = "Analyse the accepted requirements."
    context_refs: tuple[str, ...] = ("ctx:requirement-001",)
    embedding_model_ref: str = "openvino:e5-small"
    qdrant_collection_ref: str = "qdrant:autodoc-context"
    expected_output: str = "preliminary_opinion"
    depth: str = "standard"


@dataclass(frozen=True)
class VisitResult:
    visit_ref: str = "laboratory-visit:test-001"
    laboratory_ref: str = "laboratory:local-fake"
    specialist_ref: str = "specialist:requirements-analyst"
    status: str = "completed"
    output_contract_ref: str = "contract:specialist-opinion.v1"
    machine_result: object = MappingProxyType({"accepted": True})
    human_representation: str = "The requirements are internally consistent."
    confidence: float = 0.9
    evidence_refs: tuple[str, ...] = ("validation:requirements-001",)
    requested_context_refs: tuple[str, ...] = ()
    conversation_ref: str | None = None


@dataclass(frozen=True)
class OpinionFrame:
    frame_ref: str = "route-frame:opinion-test-001"
    route_ref: str = "route:deliberation/test/opinion"
    demand_frame_ref: str = "route-frame:demand-test-001"
    specialist_ref: str = "specialist:requirements-analyst"
    opinion_ref: str = "specialist-opinion:test-001"
    stance: str = "accept"
    summary: str = "Requirements are consistent."
    context_delta_refs: tuple[str, ...] = ("ctx-result:requirements-001",)
    observation_fact_refs: tuple[str, ...] = (
        "specialist-path:requirements-analyst-completed",
    )


def _descriptor() -> PortableSpecialistDescriptor:
    capability = SpecialistCapabilityContract(
        schema=SPECIALIST_CAPABILITY_SCHEMA,
        capability="requirements.analysis",
        description="Analyse requirements deterministically.",
        accepted_input_contract_refs=("contract:specialist-demand.v1",),
        produced_output_contract_refs=("contract:specialist-opinion.v1",),
    )
    profile = SpecialistExecutionProfile(
        schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
        preferred_execution_boundaries=("in_process",),
        determinism_preference="required",
    )
    binding = SpecialistLaboratoryBinding(
        schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
        specialist_ref="specialist:requirements-analyst",
        laboratory_ref="laboratory:local-fake",
        visit_modes=("resident", "visitor"),
        required_laboratory_capabilities=("deterministic.fake",),
    )
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref="specialist:requirements-analyst",
        display_name="Requirements analyst",
        specialist_version="1.0.0",
        capabilities=(capability,),
        accepted_input_contract_refs=("contract:specialist-demand.v1",),
        produced_output_contract_refs=("contract:specialist-opinion.v1",),
        execution_profile=profile,
        laboratory_bindings=(binding,),
        availability="ready",
    )


def test_projects_existing_demand_and_opinion_frames_into_conversation() -> None:
    request = VisitRequest()
    demand = build_specialist_demand_message(
        _descriptor(), request, DemandFrame(), visit_mode="resident"
    )
    opinion = build_specialist_opinion_message(
        _descriptor(),
        request,
        VisitResult(),
        OpinionFrame(),
        demand_message=demand,
    )
    conversation = SpecialistLaboratoryConversation(
        schema=SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
        conversation_ref=demand.conversation_ref,
        visit_ref=request.visit_ref,
        specialist_ref=request.specialist_ref,
        messages=(opinion, demand),
    )

    assert [item.kind for item in conversation.messages] == ["demand", "opinion"]
    assert demand.route_frame_ref == "route-frame:demand-test-001"
    assert opinion.reply_to_message_ref == demand.message_ref
    assert opinion.payload["machine_result"]["accepted"] is True
    assert validate_specialist_laboratory_conversation(conversation) == ()
    mapping = conversation.to_mapping()
    assert mapping["append_only"] is True
    assert mapping["transport_created"] is False
    assert mapping["eventbus_observation_only"] is True


def test_demand_projection_rejects_undeclared_laboratory_mode() -> None:
    with pytest.raises(
        SpecialistLaboratoryMessageContractError,
        match="visit_mode is not allowed",
    ):
        build_specialist_demand_message(
            _descriptor(), VisitRequest(), DemandFrame(), visit_mode="transfer"
        )


def test_opinion_projection_rejects_wrong_demand_frame_link() -> None:
    demand = build_specialist_demand_message(
        _descriptor(), VisitRequest(), DemandFrame(), visit_mode="resident"
    )
    wrong = OpinionFrame(demand_frame_ref="route-frame:demand-other")
    with pytest.raises(
        SpecialistLaboratoryMessageContractError,
        match="demand_frame_ref",
    ):
        build_specialist_opinion_message(
            _descriptor(),
            VisitRequest(),
            VisitResult(),
            wrong,
            demand_message=demand,
        )


def test_conversation_requires_contiguous_append_only_sequence() -> None:
    demand = build_specialist_demand_message(
        _descriptor(), VisitRequest(), DemandFrame(), visit_mode="resident"
    )
    opinion = build_specialist_opinion_message(
        _descriptor(),
        VisitRequest(),
        VisitResult(),
        OpinionFrame(),
        demand_message=demand,
        sequence_no=2,
    )
    with pytest.raises(
        SpecialistLaboratoryMessageContractError,
        match="contiguous",
    ):
        SpecialistLaboratoryConversation(
            schema=SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
            conversation_ref=demand.conversation_ref,
            visit_ref=demand.visit_ref,
            specialist_ref=demand.specialist_ref,
            messages=(demand, opinion),
        )


def test_mapping_keeps_route_and_authority_boundaries_explicit() -> None:
    demand = build_specialist_demand_message(
        _descriptor(), VisitRequest(), DemandFrame(), visit_mode="resident"
    )
    mapping = demand.to_mapping()
    assert mapping["route_ref"] == "route:deliberation/test/demand"
    assert mapping["transport_created"] is False
    assert mapping["eventbus_command"] is False
    assert mapping["durable_authority"] is False
    assert mapping["scheduler_remains_orchestrator"] is True
