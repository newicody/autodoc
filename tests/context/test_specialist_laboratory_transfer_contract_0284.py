from dataclasses import dataclass

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
    SPECIALIST_LABORATORY_MESSAGE_SCHEMA,
    SpecialistLaboratoryConversation,
    SpecialistLaboratoryMessage,
)
from context.specialist_laboratory_transfer_contract_0284 import (
    SPECIALIST_TRANSFER_REQUEST_SCHEMA,
    SpecialistLaboratoryTransferContractError,
    build_specialist_transfer_request,
    build_specialist_transfer_result,
    build_specialist_transfer_visit_plan,
    validate_specialist_transfer_chain,
)


@dataclass(frozen=True)
class SourceRequest:
    visit_ref: str = "laboratory-visit:source"
    laboratory_ref: str = "laboratory:local-fake"
    specialist_ref: str = "specialist:requirements"
    input_contract_ref: str = "contract:research-request.v1"
    expected_output_contract_ref: str = "contract:research-result.v1"
    return_route_ref: str = "specialist-path:return"
    context_refs: tuple[str, ...] = ("sql:context-1",)
    evidence_refs: tuple[str, ...] = ("artifact:request-1",)
    origin_laboratory_ref: str | None = "laboratory:local-fake"
    target_laboratory_ref: str | None = "laboratory:local-fake"
    conversation_ref: str | None = "laboratory-conversation:source"


@dataclass(frozen=True)
class SourceResult:
    visit_ref: str = "laboratory-visit:source"
    laboratory_ref: str = "laboratory:local-fake"
    specialist_ref: str = "specialist:requirements"
    status: str = "needs_specialist"
    output_contract_ref: str = "contract:research-result.v1"
    evidence_refs: tuple[str, ...] = ("validation:source",)
    requested_context_refs: tuple[str, ...] = ("ctx:extra",)
    requested_laboratory_refs: tuple[str, ...] = ("laboratory:partner-b",)
    conversation_ref: str | None = "laboratory-conversation:source"


def _descriptor() -> PortableSpecialistDescriptor:
    input_ref = "contract:research-request.v1"
    output_ref = "contract:research-result.v1"
    specialist_ref = "specialist:requirements"
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=specialist_ref,
        display_name="Requirements specialist",
        specialist_version="1.0",
        capabilities=(
            SpecialistCapabilityContract(
                schema=SPECIALIST_CAPABILITY_SCHEMA,
                capability="requirements.analysis",
                description="Analyze requirements",
                accepted_input_contract_refs=(input_ref,),
                produced_output_contract_refs=(output_ref,),
            ),
        ),
        accepted_input_contract_refs=(input_ref,),
        produced_output_contract_refs=(output_ref,),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=specialist_ref,
                laboratory_ref="laboratory:local-fake",
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=("deterministic.fake",),
            ),
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=specialist_ref,
                laboratory_ref="laboratory:partner-b",
                visit_modes=("visitor", "transfer"),
                required_laboratory_capabilities=("requirements.analysis",),
            ),
        ),
        availability="ready",
    )


def _conversation() -> SpecialistLaboratoryConversation:
    demand = SpecialistLaboratoryMessage(
        schema=SPECIALIST_LABORATORY_MESSAGE_SCHEMA,
        message_ref="laboratory-message:demand",
        conversation_ref="laboratory-conversation:source",
        visit_ref="laboratory-visit:source",
        sequence_no=0,
        kind="demand",
        specialist_ref="specialist:requirements",
        origin_laboratory_ref="laboratory:local-fake",
        target_laboratory_ref="laboratory:local-fake",
        sender_ref="laboratory:local-fake",
        recipient_ref="specialist:requirements",
        contract_ref="contract:research-request.v1",
        return_route_ref="specialist-path:return",
        human_representation="Analyze",
        payload={"request": "Analyze"},
    )
    request = SpecialistLaboratoryMessage(
        schema=SPECIALIST_LABORATORY_MESSAGE_SCHEMA,
        message_ref="laboratory-message:request-partner",
        conversation_ref="laboratory-conversation:source",
        visit_ref="laboratory-visit:source",
        sequence_no=1,
        kind="laboratory_request",
        specialist_ref="specialist:requirements",
        origin_laboratory_ref="laboratory:local-fake",
        target_laboratory_ref="laboratory:local-fake",
        sender_ref="specialist:requirements",
        recipient_ref="laboratory:local-fake",
        contract_ref="contract:research-result.v1",
        return_route_ref="specialist-path:return",
        human_representation="Visit partner B",
        payload={"target_laboratory_ref": "laboratory:partner-b"},
        reply_to_message_ref=demand.message_ref,
    )
    return SpecialistLaboratoryConversation(
        schema=SPECIALIST_LABORATORY_CONVERSATION_SCHEMA,
        conversation_ref="laboratory-conversation:source",
        visit_ref="laboratory-visit:source",
        specialist_ref="specialist:requirements",
        messages=(demand, request),
    )


def test_visit_request_preserves_identity_lineage_and_context() -> None:
    request = build_specialist_transfer_request(
        _descriptor(),
        SourceRequest(),
        SourceResult(),
        _conversation(),
        target_laboratory_ref="laboratory:partner-b",
        mode="visit",
    )
    assert request.schema == SPECIALIST_TRANSFER_REQUEST_SCHEMA
    assert request.specialist_ref == "specialist:requirements"
    assert request.origin_laboratory_ref == "laboratory:local-fake"
    assert request.target_laboratory_ref == "laboratory:partner-b"
    assert request.portable_visit_mode == "visitor"
    assert request.context_refs == ("sql:context-1", "ctx:extra")
    assert request.requested_by_message_ref == "laboratory-message:request-partner"


def test_visit_plan_maps_to_existing_laboratory_visit_fields() -> None:
    request = build_specialist_transfer_request(
        _descriptor(), SourceRequest(), SourceResult(), _conversation(),
        target_laboratory_ref="laboratory:partner-b", mode="visit"
    )
    plan = build_specialist_transfer_visit_plan(
        request, target_visit_ref="laboratory-visit:partner-b"
    )
    fields = plan.to_mapping()["laboratory_visit_request_fields"]
    assert fields["laboratory_ref"] == "laboratory:partner-b"
    assert fields["origin_laboratory_ref"] == "laboratory:local-fake"
    assert fields["target_laboratory_ref"] == "laboratory:partner-b"
    assert fields["parent_visit_ref"] == "laboratory-visit:source"
    assert plan.to_mapping()["scheduler_emit_required"] is True
    assert plan.to_mapping()["direct_provider_call_allowed"] is False


def test_completed_visit_returns_to_origin_but_transfer_stays_at_target() -> None:
    visitor = build_specialist_transfer_request(
        _descriptor(), SourceRequest(), SourceResult(), _conversation(),
        target_laboratory_ref="laboratory:partner-b", mode="visit"
    )
    visitor_plan = build_specialist_transfer_visit_plan(
        visitor, target_visit_ref="laboratory-visit:visitor"
    )
    visitor_result = build_specialist_transfer_result(
        visitor, visitor_plan, status="completed", reason="visit completed"
    )
    assert visitor_result.active_laboratory_ref == "laboratory:local-fake"

    transfer = build_specialist_transfer_request(
        _descriptor(), SourceRequest(), SourceResult(), _conversation(),
        target_laboratory_ref="laboratory:partner-b", mode="transfer"
    )
    transfer_plan = build_specialist_transfer_visit_plan(
        transfer, target_visit_ref="laboratory-visit:transfer"
    )
    transfer_result = build_specialist_transfer_result(
        transfer, transfer_plan, status="completed", reason="transfer completed"
    )
    assert transfer_result.active_laboratory_ref == "laboratory:partner-b"
    assert validate_specialist_transfer_chain(
        transfer, transfer_plan, transfer_result
    ) == ()


def test_target_must_be_requested_and_declared_compatible() -> None:
    with pytest.raises(
        SpecialistLaboratoryTransferContractError,
        match="not requested",
    ):
        build_specialist_transfer_request(
            _descriptor(), SourceRequest(), SourceResult(), _conversation(),
            target_laboratory_ref="laboratory:other", mode="visit"
        )


def test_failed_source_visit_cannot_request_transfer() -> None:
    failed = SourceResult(status="failed")
    with pytest.raises(
        SpecialistLaboratoryTransferContractError,
        match="failed source visit",
    ):
        build_specialist_transfer_request(
            _descriptor(), SourceRequest(), failed, _conversation(),
            target_laboratory_ref="laboratory:partner-b", mode="transfer"
        )


def test_result_rejects_inconsistent_active_laboratory() -> None:
    request = build_specialist_transfer_request(
        _descriptor(), SourceRequest(), SourceResult(), _conversation(),
        target_laboratory_ref="laboratory:partner-b", mode="visit"
    )
    plan = build_specialist_transfer_visit_plan(
        request, target_visit_ref="laboratory-visit:partner-b"
    )
    result = build_specialist_transfer_result(
        request, plan, status="completed", reason="done"
    )
    assert result.to_mapping()["specialist_identity_preserved"] is True
    assert result.to_mapping()["scheduler_remains_orchestrator"] is True
