from __future__ import annotations

import pytest

from context.vector_contract_indexing_plan import (
    HumanRepresentationContract,
    SpecialistInstructionContract,
    SpecialistOutputIndexingDescriptor,
    VectorCollectionRole,
    build_default_vector_collection_roles,
    build_embedded_contract_descriptor,
    build_vector_contract_instruction_packet,
    build_vector_retrieval_plan_for_specialist_request,
    collection_role_by_name,
)


def make_human_contract() -> HumanRepresentationContract:
    return HumanRepresentationContract(
        representation_ref="human-representation:technical-note",
        document_kind="technical-note",
        audience="end-user",
        sections=("hypotheses", "risks", "constraints", "next-review"),
        style_hints=("clear", "actionable"),
    )


def make_specialist_contract() -> SpecialistInstructionContract:
    return SpecialistInstructionContract(
        contract_ref="contract:thermal-preliminary-opinion",
        sql_contract_ref="sql:contract/thermal-preliminary-opinion",
        title="Thermal preliminary opinion",
        domain="thermal-analysis",
        objective="Decide what thermal constraints must be explored before production.",
        output_type="preliminary_opinion",
        human_representation=make_human_contract(),
        specialist_refs=("specialist:thermal",),
        context_refs=("sql:context/spoon", "qdrant:context_chunks_e5_384"),
        required_evidence_refs=("sql:context/spoon",),
        tags=("spoon", "baby", "thermal"),
    )


def test_default_collection_roles_are_by_usage_not_by_specialist() -> None:
    roles = build_default_vector_collection_roles()
    assert [role.role for role in roles] == [
        "context_chunks",
        "contracts",
        "specialist_outputs",
        "deliberation_signals",
        "synthesis_candidates",
    ]
    assert all(role.vector_dimension == 384 for role in roles)
    assert all(role.embedding_model_ref == "openvino:e5-small" for role in roles)
    assert all(role.to_mapping()["per_specialist_database"] is False for role in roles)
    assert all(role.to_mapping()["sql_is_authority"] is True for role in roles)


def test_collection_role_rejects_per_specialist_fragmentation() -> None:
    with pytest.raises(ValueError, match="locked vector collection roles"):
        VectorCollectionRole(
            role="thermal_specialist_private_db",
            collection_ref="qdrant:thermal",
            collection_name="thermal",
        )


def test_specialist_instruction_contract_builds_e5_passage_text() -> None:
    contract = make_specialist_contract()
    passage = contract.to_embedding_passage()
    assert passage.startswith("passage:")
    assert "thermal-analysis" in passage
    assert "preliminary_opinion" in passage
    mapping = contract.to_mapping()
    assert mapping["sql_is_authority"] is True
    assert mapping["embedding_role"] == "passage"
    assert mapping["human_representation"]["hide_specialist_provenance_by_default"] is True


def test_embedded_contract_descriptor_targets_contract_collection_only() -> None:
    contract = make_specialist_contract()
    roles = build_default_vector_collection_roles()
    descriptor = build_embedded_contract_descriptor(
        contract,
        collection_role=collection_role_by_name(roles, "contracts"),
    )
    mapping = descriptor.to_mapping()
    assert mapping["qdrant_collection_ref"] == "qdrant:contracts_e5_384"
    assert mapping["embedding_model_ref"] == "openvino:e5-small"
    assert mapping["embedding_role"] == "passage"
    assert mapping["decision_maker"] is False
    assert mapping["e5_openvino_role"] == "embedding only behind adapter"
    with pytest.raises(ValueError, match="contracts collection role"):
        build_embedded_contract_descriptor(
            contract,
            collection_role=collection_role_by_name(roles, "context_chunks"),
        )


def test_retrieval_plan_uses_query_prefix_and_cross_collection_recall() -> None:
    plan = build_vector_retrieval_plan_for_specialist_request(
        query_text="Analyse thermique d'une cuillère bébé.",
        query_context_refs=("sql:context/spoon",),
        include_roles=("contracts", "context_chunks", "specialist_outputs"),
        top_k_per_collection=5,
    )
    mapping = plan.to_mapping()
    assert plan.text_for_embedding.startswith("query:")
    assert mapping["qdrant_decides"] is False
    assert mapping["scheduler_orchestrates"] is True
    assert mapping["collection_refs"] == [
        "qdrant:contracts_e5_384",
        "qdrant:context_chunks_e5_384",
        "qdrant:specialist_outputs_e5_384",
    ]
    assert mapping["top_k_per_collection"] == 5


def test_contract_instruction_packet_enriches_scheduler_route_frame_without_github_workflow() -> None:
    packet = build_vector_contract_instruction_packet(
        demand_frame_ref="route-frame:cycle-42-round-1-demand-thermal",
        query_text="Préparer une analyse thermique préliminaire.",
        contracts=(make_specialist_contract(),),
        query_context_refs=("sql:context/spoon",),
    )
    mapping = packet.to_mapping()
    assert mapping["specialist_receives_machine_and_human_contracts"] is True
    assert mapping["github_exchange_only"] is True
    assert mapping["event_bus_observation_only"] is True
    assert mapping["retrieval_plan"]["text_for_embedding"].startswith("query:")
    assert mapping["contract_descriptors"][0]["text_for_embedding"].startswith("passage:")
    assert [target["role"] for target in mapping["output_indexing_targets"]] == [
        "specialist_outputs",
        "deliberation_signals",
        "synthesis_candidates",
    ]


def test_specialist_output_indexing_descriptor_keeps_machine_and_human_layers() -> None:
    descriptor = SpecialistOutputIndexingDescriptor(
        descriptor_ref="vector-descriptor:thermal-output-1",
        output_ref="specialist-output:thermal-1",
        sql_output_ref="sql:specialist-output/thermal-1",
        specialist_ref="specialist:thermal",
        output_type="analysis_signal",
        machine_summary="Recevable as analysis signal; needs material review.",
        human_representation_ref="human-representation:technical-note",
        evidence_refs=("sql:context/spoon",),
        bus_fact_refs=("bus:thermal/explored-axis", "specialist-path:thermal/round-1"),
    )
    mapping = descriptor.to_mapping()
    assert mapping["text_for_embedding"].startswith("passage:")
    assert mapping["sql_is_authority"] is True
    assert mapping["human_representation_ref"] == "human-representation:technical-note"
    assert mapping["bus_fact_refs"] == ["bus:thermal/explored-axis", "specialist-path:thermal/round-1"]
