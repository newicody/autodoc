from __future__ import annotations

import math
from typing import Sequence

import pytest

from src.context.sql_context_hydrator import HydratedSqlContextFragment, SqlHydratedContextBundle
from src.inference.openvino_embedding_adapter import (
    OpenVINOEmbeddingAdapter,
    OpenVINOEmbeddingPolicy,
    OpenVINOEmbeddingRuntimeTarget,
    build_embedding_texts_from_hydrated_bundle,
    build_embedding_vector,
    local_multilingual_e5_openvino_target,
)


class FakeEmbeddingExecutor:
    def embed_texts(
        self,
        texts: Sequence[str],
        *,
        target: OpenVINOEmbeddingRuntimeTarget,
        policy: OpenVINOEmbeddingPolicy,
    ) -> tuple[tuple[float, ...], ...]:
        assert target.backend_ref == "openvino:model:multilingual-e5-small"
        assert policy.expected_dimension == 3
        return tuple((1.0, 0.0, 0.0) for _ in texts)


def _bundle() -> SqlHydratedContextBundle:
    return SqlHydratedContextBundle(
        fragments=(
            HydratedSqlContextFragment(
                context_ref="sql:chunk:001",
                kind="chunk",
                title="Chunk 1",
                body="Hydrated body for embedding.",
                parent_ref="sql:document:root",
                relation="child",
            ),
            HydratedSqlContextFragment(
                context_ref="sql:fact:001",
                kind="fact",
                title="Fact 1",
                body="Fact body for embedding.",
                relation="requested",
            ),
        )
    )


def test_embedding_texts_are_built_from_hydrated_fragments_with_passage_prefix() -> None:
    texts, capped = build_embedding_texts_from_hydrated_bundle(_bundle())

    assert capped is False
    assert len(texts) == 2
    assert texts[0].source_ref == "ctx-fragment:sql:chunk:001"
    assert texts[0].text.startswith("passage: Chunk 1\n")
    assert texts[0].metadata == (
        ("context_ref", "sql:chunk:001"),
        ("kind", "chunk"),
        ("relation", "child"),
    )


def test_embedding_text_policy_caps_and_truncates_payloads() -> None:
    texts, capped = build_embedding_texts_from_hydrated_bundle(
        _bundle(),
        OpenVINOEmbeddingPolicy(max_fragments=1, max_text_chars=12),
    )

    assert capped is True
    assert len(texts) == 1
    assert texts[0].text == "passage: Chu"
    assert texts[0].truncated is True


def test_embedding_adapter_executes_injected_executor_and_returns_serializable_batch() -> None:
    target = OpenVINOEmbeddingRuntimeTarget(dimension=3)
    policy = OpenVINOEmbeddingPolicy(expected_dimension=3)
    adapter = OpenVINOEmbeddingAdapter(FakeEmbeddingExecutor(), target=target, policy=policy)

    batch = adapter.embed_hydrated_bundle(_bundle())

    assert batch.vector_count == 2
    assert batch.source_refs == ("ctx-fragment:sql:chunk:001", "ctx-fragment:sql:fact:001")
    assert batch.vectors[0].dimension == 3
    assert math.isclose(batch.vectors[0].l2_norm, 1.0)
    assert batch.to_mapping()["target"]["runtime_import"] == "src/inference/openvino_runtime.py"


def test_embedding_vector_rejects_wrong_dimension_or_non_normalized_vector() -> None:
    text = build_embedding_texts_from_hydrated_bundle(_bundle())[0][0]
    target = OpenVINOEmbeddingRuntimeTarget(dimension=3)
    policy = OpenVINOEmbeddingPolicy(expected_dimension=3)

    with pytest.raises(ValueError, match="dimension"):
        build_embedding_vector(text, (1.0, 0.0), target, policy)

    with pytest.raises(ValueError, match="normalized"):
        build_embedding_vector(text, (1.0, 1.0, 0.0), target, policy)


def test_local_target_documents_user_openvino_e5_export() -> None:
    target = local_multilingual_e5_openvino_target(device="GPU")

    assert target.device == "GPU"
    assert target.model_dir == "/home/eric/model/openvino/multilingual-e5-small"
    assert target.model_xml_path.endswith("/openvino_model.xml")
    assert target.dimension == 384
