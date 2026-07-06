from __future__ import annotations

import math

from inference.openvino_embedding_adapter import (
    OpenVINOEmbeddingPolicy,
    OpenVINOEmbeddingRuntimeTarget,
    OpenVINOEmbeddingText,
    build_embedding_vector,
    local_multilingual_e5_openvino_target,
)


def test_existing_openvino_embedding_adapter_supports_query_role_without_new_adapter() -> None:
    policy = OpenVINOEmbeddingPolicy(
        expected_dimension=4,
        require_normalized=True,
        query_prefix="query: ",
        passage_prefix="passage: ",
    )
    target = OpenVINOEmbeddingRuntimeTarget(
        model_dir="/tmp/autodoc-test-e5",
        dimension=4,
        normalized=True,
        backend_ref="openvino:model:test-e5-small",
    )
    text = OpenVINOEmbeddingText(
        source_ref="route-frame:vector-indexing-query",
        text=f"{policy.query_prefix}analyse thermique cuillere bebe",
        role="query",
        metadata=(("phase", "0134"),),
    )

    vector = build_embedding_vector(text, (0.5, 0.5, 0.5, 0.5), target, policy)

    assert vector.role == "query"
    assert vector.source_ref == "route-frame:vector-indexing-query"
    assert vector.dimension == 4
    assert vector.normalized is True
    assert math.isclose(vector.l2_norm, 1.0)
    assert vector.backend_ref == "openvino:model:test-e5-small"


def test_existing_openvino_embedding_adapter_supports_passage_role_for_projection() -> None:
    policy = OpenVINOEmbeddingPolicy(expected_dimension=4, require_normalized=True)
    target = OpenVINOEmbeddingRuntimeTarget(
        model_dir="/tmp/autodoc-test-e5",
        dimension=4,
        backend_ref="openvino:model:test-e5-small",
    )
    text = OpenVINOEmbeddingText(
        source_ref="sql:contract/thermal-preliminary-opinion",
        text="passage: contrat avis thermique preliminaire",
        role="passage",
        metadata=(("collection_role", "contracts"),),
    )

    vector = build_embedding_vector(text, (0.5, 0.5, 0.5, 0.5), target, policy)
    mapping = vector.to_mapping()

    assert mapping["role"] == "passage"
    assert mapping["source_ref"] == "sql:contract/thermal-preliminary-opinion"
    assert mapping["dimension"] == 4
    assert mapping["normalized"] is True
    assert mapping["metadata"] == {"collection_role": "contracts"}


def test_existing_local_e5_target_documents_real_model_boundary() -> None:
    target = local_multilingual_e5_openvino_target(device="CPU")
    mapping = target.to_mapping()

    assert mapping["device"] == "CPU"
    assert mapping["dimension"] == 384
    assert mapping["normalized"] is True
    assert mapping["runtime_import"] == "src/inference/openvino_runtime.py"
    assert mapping["model_xml_path"].endswith("/openvino_model.xml")
