from __future__ import annotations

from typing import Sequence

import pytest

from src.inference.openvino_embedding_adapter import (
    OpenVINOEmbeddingBatch,
    OpenVINOEmbeddingRuntimeTarget,
    OpenVINOEmbeddingVector,
)
from src.inference.qdrant_projection_adapter import (
    QdrantProjectionAdapter,
    QdrantProjectionExecutor,
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
    QdrantRecallHit,
    QdrantRecallQuery,
    QdrantRecallResult,
    build_qdrant_projection_batch,
    build_qdrant_projection_point,
    local_qdrant_projection_target,
    unique_sql_context_refs_from_recall,
)


class FakeQdrantExecutor(QdrantProjectionExecutor):
    def __init__(self) -> None:
        self.upserted: tuple[str, ...] = ()

    def upsert_points(
        self,
        points: Sequence,
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
    ) -> QdrantProjectionWriteResult:
        assert target.collection_name == "autodoc_context_embeddings"
        assert policy.max_points == 4
        self.upserted = tuple(point.point_id for point in points)
        return QdrantProjectionWriteResult(target=target, point_ids=self.upserted)

    def search_vector(
        self,
        vector: Sequence[float],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
        query: QdrantRecallQuery,
    ) -> QdrantRecallResult:
        assert tuple(vector) == (1.0, 0.0, 0.0)
        assert query.query_ref == "embedding:query:001"
        return QdrantRecallResult(
            target=target,
            query=query,
            hits=(
                QdrantRecallHit(point_id="qdrant-point:001", sql_context_ref="sql:chunk:001", score=0.99),
                QdrantRecallHit(point_id="qdrant-point:002", sql_context_ref="sql:fact:001", score=0.80),
            ),
        )


def _embedding_batch() -> OpenVINOEmbeddingBatch:
    return OpenVINOEmbeddingBatch(
        target=OpenVINOEmbeddingRuntimeTarget(dimension=3),
        vectors=(
            OpenVINOEmbeddingVector(
                embedding_ref="embedding:passage:001",
                source_ref="ctx-fragment:sql:chunk:001",
                vector=(1.0, 0.0, 0.0),
                backend_ref="openvino:model:test",
                metadata=(
                    ("context_ref", "sql:chunk:001"),
                    ("kind", "chunk"),
                    ("relation", "child"),
                ),
            ),
            OpenVINOEmbeddingVector(
                embedding_ref="embedding:passage:002",
                source_ref="ctx-fragment:sql:fact:001",
                vector=(0.0, 1.0, 0.0),
                backend_ref="openvino:model:test",
                metadata=(("context_ref", "sql:fact:001"), ("kind", "fact")),
            ),
        ),
    )


def test_projection_point_preserves_sql_ref_in_payload() -> None:
    point = build_qdrant_projection_point(
        _embedding_batch().vectors[0],
        QdrantProjectionTarget(vector_dimension=3),
    )

    assert point.point_id.startswith("qdrant-point:")
    assert point.sql_context_ref == "sql:chunk:001"
    assert point.dimension == 3
    assert dict(point.payload)["sql_context_ref"] == "sql:chunk:001"
    assert dict(point.payload)["qdrant_backend_ref"] == "qdrant:collection:autodoc_context_embeddings"


def test_projection_batch_is_bounded_and_serializable() -> None:
    batch = build_qdrant_projection_batch(
        _embedding_batch(),
        QdrantProjectionTarget(vector_dimension=3),
        QdrantProjectionPolicy(max_points=1),
    )

    assert batch.capped is True
    assert batch.point_count == 1
    assert batch.sql_context_refs == ("sql:chunk:001",)
    assert batch.to_mapping()["target"]["storage_path"] == "/srv/autodoc/qdrant/storage"


def test_projection_adapter_uses_injected_executor_without_importing_qdrant_client() -> None:
    executor = FakeQdrantExecutor()
    adapter = QdrantProjectionAdapter(
        executor,
        target=QdrantProjectionTarget(vector_dimension=3),
        policy=QdrantProjectionPolicy(max_points=4),
    )

    result = adapter.upsert_embedding_batch(_embedding_batch())

    assert result.acknowledged is True
    assert result.point_count == 2
    assert executor.upserted == result.point_ids


def test_recall_result_returns_unique_sql_refs_for_rehydration() -> None:
    target = QdrantProjectionTarget(vector_dimension=3)
    query = QdrantRecallQuery(query_ref="embedding:query:001", limit=3)
    result = QdrantRecallResult(
        target=target,
        query=query,
        hits=(
            QdrantRecallHit(point_id="qdrant-point:001", sql_context_ref="sql:chunk:001", score=0.99),
            QdrantRecallHit(point_id="qdrant-point:002", sql_context_ref="sql:chunk:001", score=0.90),
            QdrantRecallHit(point_id="qdrant-point:003", sql_context_ref="sql:fact:001", score=0.75),
        ),
    )

    assert unique_sql_context_refs_from_recall(result) == ("sql:chunk:001", "sql:fact:001")
    assert unique_sql_context_refs_from_recall(result, max_refs=1) == ("sql:chunk:001",)
    assert result.to_mapping()["sql_context_refs"] == ["sql:chunk:001", "sql:fact:001"]


def test_projection_rejects_wrong_dimension_and_missing_sql_ref() -> None:
    target = QdrantProjectionTarget(vector_dimension=4)
    with pytest.raises(ValueError, match="dimension"):
        build_qdrant_projection_point(_embedding_batch().vectors[0], target)

    missing = OpenVINOEmbeddingVector(
        embedding_ref="embedding:passage:missing",
        source_ref="ctx-fragment:doc:missing",
        vector=(1.0, 0.0, 0.0),
        backend_ref="openvino:model:test",
    )
    with pytest.raises(ValueError, match="sql context_ref"):
        build_qdrant_projection_point(missing, QdrantProjectionTarget(vector_dimension=3))


def test_adapter_recall_delegates_to_injected_executor() -> None:
    adapter = QdrantProjectionAdapter(
        FakeQdrantExecutor(),
        target=QdrantProjectionTarget(vector_dimension=3),
        policy=QdrantProjectionPolicy(max_points=4),
    )

    result = adapter.recall_by_vector((1.0, 0.0, 0.0), QdrantRecallQuery(query_ref="embedding:query:001"))

    assert result.sql_context_refs == ("sql:chunk:001", "sql:fact:001")


def test_local_target_documents_user_qdrant_installation() -> None:
    target = local_qdrant_projection_target(vector_dimension=384)

    assert target.endpoint_ref == "qdrant:local:6333"
    assert target.storage_path == "/srv/autodoc/qdrant/storage"
    assert target.snapshots_path == "/srv/autodoc/qdrant/snapshots"
    assert target.vector_dimension == 384
