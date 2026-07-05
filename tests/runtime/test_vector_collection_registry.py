from __future__ import annotations

import pytest

from context.vector_collection_registry import (
    VectorCollectionRegistry,
    build_default_vector_collection_registry,
)
from context.vector_contract_indexing_plan import build_default_vector_collection_roles


def test_default_registry_uses_one_qdrant_instance_and_role_collections() -> None:
    registry = build_default_vector_collection_registry()
    mapping = registry.to_mapping()
    assert mapping["one_qdrant_instance_multiple_role_collections"] is True
    assert mapping["per_specialist_database"] is False
    assert mapping["scheduler_orchestrates"] is True
    assert mapping["e5_openvino_role"] == "embedding only behind adapter"
    assert mapping["qdrant_role"] == "projection and recall only"
    assert mapping["role_names"] == [
        "context_chunks",
        "contracts",
        "specialist_outputs",
        "deliberation_signals",
        "synthesis_candidates",
    ]


def test_ensure_plan_is_adapter_executable_later_not_runtime_client() -> None:
    registry = build_default_vector_collection_registry()
    plan = registry.ensure_plan()
    mapping = plan.to_mapping()
    assert mapping["runtime_client_required_here"] is False
    assert mapping["adapter_executes_later"] is True
    assert [item["collection_name"] for item in mapping["items"]] == [
        "context_chunks_e5_384",
        "contracts_e5_384",
        "specialist_outputs_e5_384",
        "deliberation_signals_e5_384",
        "synthesis_candidates_e5_384",
    ]
    assert all(item["qdrant_runtime_client"] is False for item in mapping["items"])
    assert all(item["sql_is_authority"] is True for item in mapping["items"])


def test_registry_rejects_duplicate_roles_and_per_specialist_names() -> None:
    roles = build_default_vector_collection_roles()
    with pytest.raises(ValueError, match="collection roles must be unique"):
        VectorCollectionRegistry(
            registry_ref="vector-registry:duplicate",
            qdrant_instance_ref="qdrant:local-autodoc",
            collection_roles=(roles[0], roles[0]),
        )
    bad_role = roles[0].__class__(
        role="context_chunks",
        collection_ref="qdrant:thermal_private_context",
        collection_name="thermal_specialist_context",
    )
    with pytest.raises(ValueError, match="per-specialist collection names"):
        VectorCollectionRegistry(
            registry_ref="vector-registry:bad",
            qdrant_instance_ref="qdrant:local-autodoc",
            collection_roles=(bad_role,),
        )


def test_route_point_selects_collection_by_contract_and_output_kind() -> None:
    registry = build_default_vector_collection_registry()
    contract_point = registry.route_point(source_ref="contract:thermal-preliminary-opinion", output_kind="contract")
    assert contract_point.to_mapping()["collection_role"] == "contracts"
    specialist_point = registry.route_point(
        source_ref="sql:specialist-output/thermal-1",
        output_kind="preliminary_opinion",
        specialist_ref="specialist:thermal",
    )
    specialist_mapping = specialist_point.to_mapping()
    assert specialist_mapping["collection_role"] == "specialist_outputs"
    assert specialist_mapping["payload_refs"] == ["sql:specialist-output/thermal-1", "specialist:thermal"]
    assert specialist_mapping["qdrant_payload_is_lightweight"] is True


def test_route_point_selects_bus_signals_and_synthesis_candidates() -> None:
    registry = build_default_vector_collection_registry()
    signal = registry.route_point(source_ref="bus:thermal/explored-axis", output_kind="analysis_signal")
    synthesis = registry.route_point(source_ref="ctx-result:cycle-42/final-draft", output_kind="final_synthesis_candidate")
    assert signal.to_mapping()["collection_role"] == "deliberation_signals"
    assert synthesis.to_mapping()["collection_role"] == "synthesis_candidates"


def test_route_point_rejects_unknown_source() -> None:
    registry = build_default_vector_collection_registry()
    with pytest.raises(ValueError, match="cannot route"):
        registry.route_point(source_ref="artifact:unknown", output_kind="unclassified")
