from __future__ import annotations

from dataclasses import dataclass

import pytest

from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    HYBRID_FILTER_SCHEMA,
    HYBRID_QUERY_SCHEMA,
    DenseQueryEmbedding,
    HybridRetrievalFilter,
    HybridRetrievalQuery,
    build_sparse_lexical_query,
)
from context.love_qdrant_hybrid_query_adapter_0287 import (
    build_love_qdrant_hybrid_query_adapter,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)
from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    QdrantClientExecutionError,
    QdrantClientProjectionExecutor,
)


class _Filter:
    def __init__(self, **value):
        self.value = value


@dataclass
class _SparseVector:
    indices: list[int]
    values: list[float]


class _Models:
    Filter = _Filter
    SparseVector = _SparseVector


@dataclass
class _Point:
    id: str
    score: float
    payload: dict[str, object]


@dataclass
class _Response:
    points: list[_Point]


class _Client:
    def __init__(self, points):
        self.points = points
        self.calls = []

    def query_points(self, **kwargs):
        self.calls.append(kwargs)
        return _Response(list(self.points))


def _payload() -> dict[str, object]:
    return {
        "autodoc_point_ref": "qdrant-point:love-1",
        "sql_ref": "context-object:love-1",
        "source_ref": "context-object:love-1",
        "source_content_digest": "sha256:" + "1" * 64,
        "context_revision_ref": "context-revision:love-base",
        "branch_ref": "context-branch:main",
        "project_ref": "project:newicody-autodoc",
        "security_scope": "scope:local",
        "valid": True,
        "superseded_by": "",
        "artifact_kind": "analysis",
        "contribution_kind": "domain_analysis",
        "document_ref": "document:love-1",
    }


def _executor(points=(_Point("1", 0.9, _payload()),)):
    client = _Client(points)
    executor = QdrantClientProjectionExecutor(
        client=client,
        models_module=_Models,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(
            policy_decision_id="policy:love-r9",
            allow_search=True,
        ),
    )
    return executor, client


def _collection() -> QdrantCollectionProfile:
    return QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref="qdrant-profile:love-hybrid-v1",
        collection_name="autodoc_context_current",
        collection_alias="autodoc_context_current",
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(
            QdrantNamedVectorProfile(
                schema=QDRANT_NAMED_VECTOR_SCHEMA,
                vector_name="dense_e5_v1",
                vector_kind="dense",
                embedding_profile_ref="embedding-profile:e5-small-v1",
                model_ref="model:multilingual-e5-small",
                model_revision="installed",
                dimension=384,
                distance="Cosine",
                normalized=True,
            ),
            QdrantNamedVectorProfile(
                schema=QDRANT_NAMED_VECTOR_SCHEMA,
                vector_name="sparse_lexical_v1",
                vector_kind="sparse",
                embedding_profile_ref="embedding-profile:sparse-lexical-v1",
                model_ref="model:sparse-lexical",
                model_revision="1",
                dimension=None,
                distance=None,
                normalized=None,
                hnsw_enabled=False,
            ),
        ),
        payload_indexes=build_canonical_payload_indexes(),
    )


def _query() -> HybridRetrievalQuery:
    return HybridRetrievalQuery(
        schema=HYBRID_QUERY_SCHEMA,
        query_ref="retrieval-query:love-r9",
        task_ref="specialist-task:love-r9",
        query_text="amour confiance",
        filter=HybridRetrievalFilter(
            schema=HYBRID_FILTER_SCHEMA,
            context_revision_ref="context-revision:love-base",
            branch_ref="context-branch:main",
            project_ref="project:newicody-autodoc",
            security_scope="scope:local",
        ),
        dense_candidate_limit=4,
        sparse_candidate_limit=3,
        final_limit=3,
    )


def test_named_dense_query_uses_sdk_using_and_reference_only_payload() -> None:
    executor, client = _executor()
    adapter = build_love_qdrant_hybrid_query_adapter(executor)
    embedding = DenseQueryEmbedding(
        schema=DENSE_QUERY_EMBEDDING_SCHEMA,
        query_ref="retrieval-query:love-r9",
        vector_name="dense_e5_v1",
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
        backend_ref="openvino:multilingual-e5-small",
        values=(1.0,) + (0.0,) * 383,
    )

    candidates = adapter.search_dense(
        embedding,
        query=_query(),
        collection=_collection(),
    )

    assert candidates[0].sql_ref == "context-object:love-1"
    assert candidates[0].payload["valid"] is True
    assert client.calls[0]["using"] == "dense_e5_v1"
    assert client.calls[0]["with_vectors"] is False
    assert isinstance(client.calls[0]["query_filter"], _Filter)


def test_named_sparse_query_uses_sparse_vector_and_limit() -> None:
    executor, client = _executor()
    adapter = build_love_qdrant_hybrid_query_adapter(executor)
    sparse = build_sparse_lexical_query(
        "amour confiance",
        query_ref="retrieval-query:love-r9",
    )

    candidates = adapter.search_sparse(
        sparse,
        query=_query(),
        collection=_collection(),
    )

    call = client.calls[0]
    assert call["using"] == "sparse_lexical_v1"
    assert call["limit"] == 3
    assert isinstance(call["query"], _SparseVector)
    assert candidates[0].source == "sparse"


def test_effect_gate_denies_search() -> None:
    client = _Client(())
    executor = QdrantClientProjectionExecutor(
        client=client,
        models_module=_Models,
        config=QdrantClientConnectionConfig(),
        gate=QdrantClientEffectGate(
            policy_decision_id="policy:love-r9-denied",
            allow_search=False,
        ),
    )

    with pytest.raises(QdrantClientExecutionError, match="gate_denied"):
        executor.query_named_dense(
            (1.0, 0.0),
            collection_name="autodoc_context_current",
            vector_name="dense_e5_v1",
            limit=1,
            filter_mapping={"must": []},
        )


def test_forbidden_authoritative_content_fails_closed() -> None:
    bad = _payload()
    bad["body"] = "authoritative content"
    executor, _ = _executor((_Point("1", 0.9, bad),))

    with pytest.raises(QdrantClientExecutionError, match="forbidden_payload"):
        executor.query_named_dense(
            (1.0, 0.0),
            collection_name="autodoc_context_current",
            vector_name="dense_e5_v1",
            limit=1,
            filter_mapping={"must": []},
        )
