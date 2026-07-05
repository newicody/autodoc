from __future__ import annotations

import pytest

from context.vector_indexing_job_plan import (
    VectorIndexableItem,
    build_indexable_item_from_mapping,
    build_vector_indexing_job_plan,
)


def test_build_vector_indexing_plan_routes_items_by_role_collections() -> None:
    items = (
        build_indexable_item_from_mapping(
            source_ref="sql:chunk/thermal-1",
            output_kind="context_chunk",
            text="conductivite thermique acier inox",
        ),
        build_indexable_item_from_mapping(
            source_ref="contract:thermal-preliminary-opinion",
            output_kind="contract",
            text="contrat avis thermique preliminaire",
        ),
        build_indexable_item_from_mapping(
            source_ref="sql:specialist-output/thermal-1",
            output_kind="preliminary_opinion",
            text="avis thermique possible avec contraintes",
            specialist_ref="specialist:thermal",
        ),
        build_indexable_item_from_mapping(
            source_ref="bus:thermal/explored-axis",
            output_kind="analysis_signal",
            text="signal exploration axe thermique",
        ),
        build_indexable_item_from_mapping(
            source_ref="ctx-result:cycle-42/final-draft",
            output_kind="final_synthesis_candidate",
            text="candidat synthese finale lisible humain",
        ),
    )
    plan = build_vector_indexing_job_plan(items)
    mapping = plan.to_mapping()
    assert mapping["scheduler_is_orchestrator"] is True
    assert mapping["parallel_local_orchestrator"] is False
    assert mapping["e5_openvino_role"] == "embedding only behind adapter"
    assert mapping["qdrant_role"] == "projection and recall only"
    assert mapping["sql_is_authority"] is True
    assert mapping["collection_refs"] == [
        "qdrant:context_chunks_e5_384",
        "qdrant:contracts_e5_384",
        "qdrant:specialist_outputs_e5_384",
        "qdrant:deliberation_signals_e5_384",
        "qdrant:synthesis_candidates_e5_384",
    ]
    assert mapping["item_count"] == 5
    assert len(mapping["embedding_jobs"]) == 5
    assert len(mapping["projection_jobs"]) == 5


def test_vector_indexing_route_frames_are_dev_shm_multitask_interface() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="sql:chunk/wooden-spoon",
        output_kind="context_chunk",
        text="bois alimentaire texture bebe",
    )
    plan = build_vector_indexing_job_plan((item,))
    embedding_job = plan.to_mapping()["embedding_jobs"][0]
    request_frame = embedding_job["request_frame"]
    assert request_frame["dev_shm_path"].startswith("/dev/shm/autodoc/routes/vector-indexing/default/")
    assert request_frame["data_plane"] == "dev_shm_multitask_interface"
    assert request_frame["future_grid_seam"] is True
    assert request_frame["durable_authority"] is False


def test_vector_indexing_plan_is_bounded_and_caps_items() -> None:
    items = tuple(
        build_indexable_item_from_mapping(
            source_ref=f"sql:chunk/{index}",
            output_kind="context_chunk",
            text=f"chunk {index}",
        )
        for index in range(4)
    )
    plan = build_vector_indexing_job_plan(items, max_items=2)
    assert plan.item_count == 2
    assert plan.capped is True
    assert plan.to_mapping()["batch_command"]["bounded_indexing_batch"] is True


def test_vector_indexable_item_requires_e5_prefix_for_direct_construction() -> None:
    with pytest.raises(ValueError, match="text_for_embedding must start"):
        VectorIndexableItem(
            source_ref="sql:chunk/no-prefix",
            output_kind="context_chunk",
            text_for_embedding="missing prefix",
        )


def test_query_item_uses_query_prefix_and_routes_contract_retrieval_signal() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="bus:server/refined-demand",
        output_kind="analysis_signal",
        text="chercher contrats pertinents pour analyse thermique",
        embedding_role="query",
    )
    assert item.text_for_embedding.startswith("query: ")
    plan = build_vector_indexing_job_plan((item,))
    projection_mapping = plan.to_mapping()["projection_jobs"][0]
    assert projection_mapping["collection_role"] == "deliberation_signals"
    assert projection_mapping["qdrant_decides"] is False


def test_specialist_ref_stays_payload_filter_not_collection_name() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="sql:specialist-output/material-1",
        output_kind="work_product",
        text="proposition cuillere bois alimentaire",
        specialist_ref="specialist:material",
    )
    plan = build_vector_indexing_job_plan((item,))
    projection_mapping = plan.to_mapping()["projection_jobs"][0]
    assert projection_mapping["collection_ref"] == "qdrant:specialist_outputs_e5_384"
    assert projection_mapping["routing_plan"]["specialist_ref"] == "specialist:material"
    assert projection_mapping["routing_plan"]["collection_name"] == "specialist_outputs_e5_384"
