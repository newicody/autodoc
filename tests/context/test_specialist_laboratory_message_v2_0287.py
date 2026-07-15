from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
    SPECIALIST_EXCHANGE_ERROR_SCHEMA,
    SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
    SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
    SpecialistArtifactReference,
    SpecialistExchangeError,
    SpecialistLaboratoryConversationV2,
    SpecialistLaboratoryMessageV2,
    SpecialistLaboratoryMessageV2ContractError,
    build_completion_message_v2,
    build_error_message_v2,
    compute_payload_sha256,
    stable_idempotency_key,
)


def _artifact(*, suffix: str = "analysis") -> SpecialistArtifactReference:
    return SpecialistArtifactReference(
        schema=SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
        artifact_ref=f"artifact:{suffix}",
        artifact_schema="missipy.specialist.deep_analysis_contribution.v1",
        producer_ref="specialist:love-concept-and-affect-analyst",
        producer_visit_ref="laboratory-visit:love-1",
        storage_ref=f"sql:artifact:{suffix}",
        content_sha256=hashlib.sha256(suffix.encode()).hexdigest(),
        media_type="application/json",
        byte_count=128,
        evidence_refs=("ctx:source-love-note",),
        provenance_refs=("laboratory-visit:love-1",),
    )


def _message(
    *,
    sequence_no: int = 0,
    kind: str = "demand",
    message_ref: str = "laboratory-message:root",
    visit_ref: str = "laboratory-visit:love-1",
    specialist_ref: str = "specialist:love-concept-and-affect-analyst",
    sender_ref: str = "laboratory:love-studies-local",
    recipient_ref: str = "specialist:love-concept-and-affect-analyst",
    reply_to_message_ref: str | None = None,
    parent_visit_ref: str | None = None,
    continuation_of_message_ref: str | None = None,
    artifact_refs: tuple[SpecialistArtifactReference, ...] = (),
    error: SpecialistExchangeError | None = None,
) -> SpecialistLaboratoryMessageV2:
    payload = {"objective": "Analyse the provided material", "sequence": sequence_no}
    return SpecialistLaboratoryMessageV2(
        schema=SPECIALIST_LABORATORY_MESSAGE_V2_SCHEMA,
        message_ref=message_ref,
        conversation_ref="laboratory-conversation:love-study",
        visit_ref=visit_ref,
        sequence_no=sequence_no,
        kind=kind,  # type: ignore[arg-type]
        specialist_ref=specialist_ref,
        origin_laboratory_ref="laboratory:love-studies-local",
        target_laboratory_ref="laboratory:love-studies-local",
        sender_ref=sender_ref,
        recipient_ref=recipient_ref,
        payload_contract_ref="contract:missipy.research.correlated_work_package.v1",
        return_route_ref="route:github-issue:42",
        correlation_ref="correlation:love-study-42",
        idempotency_key=stable_idempotency_key(message_ref, str(sequence_no)),
        human_representation="Human-readable exchange",
        payload=payload,
        payload_sha256=compute_payload_sha256(payload),
        reply_to_message_ref=reply_to_message_ref,
        parent_visit_ref=parent_visit_ref,
        continuation_of_message_ref=continuation_of_message_ref,
        context_refs=("research-work-package:love-42",),
        evidence_refs=("ctx:source-love-note",),
        artifact_refs=artifact_refs,
        error=error,
    )


def test_payload_digest_and_artifact_reference_are_serialized() -> None:
    artifact = _artifact()
    message = _message(artifact_refs=(artifact,))

    payload = message.to_mapping()

    assert payload["payload_sha256"] == compute_payload_sha256(message.payload)
    assert payload["artifact_refs"][0]["content_sha256"] == artifact.content_sha256
    assert payload["transport_created"] is False
    assert payload["scheduler_remains_orchestrator"] is True


def test_tampered_payload_digest_is_rejected() -> None:
    message = _message()

    with pytest.raises(
        SpecialistLaboratoryMessageV2ContractError,
        match="payload_sha256",
    ):
        replace(message, payload_sha256="0" * 64)


def test_cross_visit_conversation_can_continue_to_second_specialist() -> None:
    root = _message()
    first_analysis = _message(
        sequence_no=1,
        kind="analysis",
        message_ref="laboratory-message:first-analysis",
        sender_ref="specialist:love-concept-and-affect-analyst",
        recipient_ref="laboratory:love-studies-local",
        reply_to_message_ref=root.message_ref,
        artifact_refs=(_artifact(),),
    )
    first_completion = build_completion_message_v2(
        demand_message=root,
        message_ref="laboratory-message:first-complete",
        sequence_no=2,
        specialist_ref=root.specialist_ref,
        visit_ref=root.visit_ref,
        human_representation="First analysis completed",
        artifact_refs=(_artifact(),),
    )
    second_demand = _message(
        sequence_no=3,
        message_ref="laboratory-message:second-demand",
        visit_ref="laboratory-visit:love-2",
        specialist_ref="specialist:love-relational-dynamics-analyst",
        recipient_ref="specialist:love-relational-dynamics-analyst",
        reply_to_message_ref=first_completion.message_ref,
        parent_visit_ref=root.visit_ref,
        continuation_of_message_ref=first_completion.message_ref,
    )
    second_completion = build_completion_message_v2(
        demand_message=second_demand,
        message_ref="laboratory-message:second-complete",
        sequence_no=4,
        specialist_ref=second_demand.specialist_ref,
        visit_ref=second_demand.visit_ref,
        human_representation="Second analysis completed",
        artifact_refs=(),
    )

    conversation = SpecialistLaboratoryConversationV2(
        schema=SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
        conversation_ref=root.conversation_ref,
        correlation_ref=root.correlation_ref,
        return_route_ref=root.return_route_ref,
        messages=(
            root,
            first_analysis,
            first_completion,
            second_demand,
            second_completion,
        ),
        closed=True,
    )

    mapping = conversation.to_mapping()
    assert mapping["visit_refs"] == [
        "laboratory-visit:love-1",
        "laboratory-visit:love-2",
    ]
    assert mapping["specialist_refs"] == [
        "specialist:love-concept-and-affect-analyst",
        "specialist:love-relational-dynamics-analyst",
    ]
    assert mapping["cross_visit_continuation_supported"] is True


def test_closed_conversation_requires_terminal_final_message() -> None:
    root = _message()

    with pytest.raises(
        SpecialistLaboratoryMessageV2ContractError,
        match="closed conversation",
    ):
        SpecialistLaboratoryConversationV2(
            schema=SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
            conversation_ref=root.conversation_ref,
            correlation_ref=root.correlation_ref,
            return_route_ref=root.return_route_ref,
            messages=(root,),
            closed=True,
        )


def test_error_message_is_normalized_and_strict() -> None:
    root = _message()
    error = SpecialistExchangeError(
        schema=SPECIALIST_EXCHANGE_ERROR_SCHEMA,
        error_code="missing_context",
        retryable=True,
        human_message="Required context is missing",
        failed_message_ref=root.message_ref,
        requested_action="supply_context",
        details={"context_ref": "ctx:missing"},
    )
    terminal = build_error_message_v2(
        demand_message=root,
        message_ref="laboratory-message:error",
        sequence_no=1,
        specialist_ref=root.specialist_ref,
        visit_ref=root.visit_ref,
        error=error,
    )
    conversation = SpecialistLaboratoryConversationV2(
        schema=SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
        conversation_ref=root.conversation_ref,
        correlation_ref=root.correlation_ref,
        return_route_ref=root.return_route_ref,
        messages=(root, terminal),
        closed=True,
    )

    assert conversation.messages[-1].error is error
    assert conversation.messages[-1].to_mapping()["terminal"] is True

    with pytest.raises(
        SpecialistLaboratoryMessageV2ContractError,
        match="retryable",
    ):
        replace(error, retryable=1)  # type: ignore[arg-type]


def test_conversation_rejects_duplicate_idempotency_keys() -> None:
    root = _message()
    analysis = _message(
        sequence_no=1,
        kind="analysis",
        message_ref="laboratory-message:analysis",
        sender_ref=root.specialist_ref,
        recipient_ref=root.target_laboratory_ref,
        reply_to_message_ref=root.message_ref,
    )
    analysis = replace(analysis, idempotency_key=root.idempotency_key)

    with pytest.raises(
        SpecialistLaboratoryMessageV2ContractError,
        match="idempotency",
    ):
        SpecialistLaboratoryConversationV2(
            schema=SPECIALIST_LABORATORY_CONVERSATION_V2_SCHEMA,
            conversation_ref=root.conversation_ref,
            correlation_ref=root.correlation_ref,
            return_route_ref=root.return_route_ref,
            messages=(root, analysis),
        )
