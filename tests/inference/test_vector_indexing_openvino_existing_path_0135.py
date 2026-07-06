from __future__ import annotations

from context.vector_indexing_job_plan import (
    build_indexable_item_from_mapping,
    build_vector_indexing_job_plan,
)
from inference.openvino_embedding_adapter import (
    OpenVINOEmbeddingPolicy,
    OpenVINOEmbeddingRuntimeTarget,
    OpenVINOEmbeddingText,
    build_embedding_vector,
)


def _unit_vector_384() -> tuple[float, ...]:
    return (1.0,) + (0.0,) * 383


def test_vector_indexing_embedding_job_is_compatible_with_existing_openvino_text_contract() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="ctx-fragment:0135-openvino-route",
        output_kind="context_chunk",
        text="route handler writes a vector indexing request",
        embedding_role="passage",
    )
    plan = build_vector_indexing_job_plan((item,))
    job = plan.embedding_jobs[0]

    text = OpenVINOEmbeddingText(
        source_ref=job.item.source_ref,
        text=job.item.text_for_embedding,
        role=job.item.embedding_role,
        title="0135 vector indexing job",
        metadata=(
            ("job_ref", job.job_ref),
            ("request_frame", job.request_frame.route_ref),
            ("result_frame", job.result_frame.route_ref),
        ),
    )

    assert text.text.startswith("passage: ")
    assert text.role == "passage"
    assert text.source_ref == job.item.source_ref
    assert dict(text.metadata)["job_ref"] == job.job_ref


def test_vector_indexing_job_raw_vector_validates_through_existing_openvino_vector_contract() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="contract:0135-openvino-vector",
        output_kind="contract",
        text="Scheduler queues embedding work; OpenVINO adapter executes later",
        embedding_role="passage",
    )
    plan = build_vector_indexing_job_plan((item,))
    job = plan.embedding_jobs[0]
    target = OpenVINOEmbeddingRuntimeTarget(dimension=job.expected_dimension)
    policy = OpenVINOEmbeddingPolicy(expected_dimension=job.expected_dimension)
    text = OpenVINOEmbeddingText(
        source_ref=job.item.source_ref,
        text=job.item.text_for_embedding,
        role=job.item.embedding_role,
        metadata=(("job_ref", job.job_ref),),
    )

    vector = build_embedding_vector(text, _unit_vector_384(), target, policy)

    assert vector.dimension == job.expected_dimension == 384
    assert vector.role == "passage"
    assert vector.backend_ref == target.backend_ref
    assert vector.normalized is True
    assert vector.source_ref == item.source_ref


def test_vector_indexing_query_role_keeps_existing_e5_prefix_boundary() -> None:
    item = build_indexable_item_from_mapping(
        source_ref="scheduler-trace:0135-openvino-query",
        output_kind="scheduler_trace",
        text="find the most relevant route pressure signal",
        embedding_role="query",
    )
    plan = build_vector_indexing_job_plan((item,))
    job = plan.embedding_jobs[0]

    text = OpenVINOEmbeddingText(
        source_ref=job.item.source_ref,
        text=job.item.text_for_embedding,
        role=job.item.embedding_role,
        metadata=(("job_ref", job.job_ref),),
    )

    assert text.text.startswith("query: ")
    assert text.role == "query"
    assert job.to_mapping()["runtime_import_required_here"] is False
    assert job.to_mapping()["openvino_adapter_executes_later"] is True
