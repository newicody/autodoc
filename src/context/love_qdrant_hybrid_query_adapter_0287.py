"""Qdrant hybrid-query adapter for the installed love runtime.

The adapter maps the existing hybrid retrieval protocol to the public named
dense/sparse query surface of the existing qdrant-client execution membrane.
It does not construct a client, collection, Scheduler, SQL store or embedding
pipeline. Qdrant returns reference-only payloads and SQL remains authoritative.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from context.hybrid_retrieval_sql_rehydration_0287 import (
    HYBRID_CANDIDATE_SCHEMA,
    DenseQueryEmbedding,
    HybridRetrievalCandidate,
    HybridRetrievalError,
    HybridRetrievalQuery,
    SparseLexicalQuery,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile


LOVE_QDRANT_HYBRID_QUERY_ADAPTER_SCHEMA = (
    "missipy.love.qdrant_hybrid_query_adapter.v1"
)


class QdrantReferenceHitLike(Protocol):
    point_id: str
    sql_ref: str
    source_ref: str
    score: float
    payload: Mapping[str, object]


class NamedQdrantQueryExecutor(Protocol):
    def query_named_dense(
        self,
        vector: Sequence[float],
        *,
        collection_name: str,
        vector_name: str,
        limit: int,
        filter_mapping: Mapping[str, object],
    ) -> Sequence[QdrantReferenceHitLike]: ...

    def query_named_sparse(
        self,
        indices: Sequence[int],
        values: Sequence[float],
        *,
        collection_name: str,
        vector_name: str,
        limit: int,
        filter_mapping: Mapping[str, object],
    ) -> Sequence[QdrantReferenceHitLike]: ...


@dataclass(frozen=True, slots=True)
class LoveQdrantHybridQueryAdapterReceipt:
    schema: str
    dense_vector_name: str
    sparse_vector_name: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "dense_vector_name": self.dense_vector_name,
            "sparse_vector_name": self.sparse_vector_name,
            "boundaries": {
                "existing_qdrant_executor_reused": True,
                "named_dense_query_supported": True,
                "named_sparse_query_supported": True,
                "reference_only_payloads": True,
                "sql_remains_authority": True,
                "qdrant_write_performed": False,
                "scheduler_constructed": False,
            },
        }


class LoveQdrantHybridQueryAdapter:
    """Implement the existing dense+sparse Qdrant hybrid query protocol."""

    def __init__(self, executor: NamedQdrantQueryExecutor) -> None:
        self._executor = executor

    def receipt(
        self,
        *,
        dense_vector_name: str,
        sparse_vector_name: str,
    ) -> LoveQdrantHybridQueryAdapterReceipt:
        return LoveQdrantHybridQueryAdapterReceipt(
            schema=LOVE_QDRANT_HYBRID_QUERY_ADAPTER_SCHEMA,
            dense_vector_name=dense_vector_name,
            sparse_vector_name=sparse_vector_name,
        )

    def search_dense(
        self,
        embedding: DenseQueryEmbedding,
        *,
        query: HybridRetrievalQuery,
        collection: QdrantCollectionProfile,
    ) -> tuple[HybridRetrievalCandidate, ...]:
        profile = collection.vector(embedding.vector_name)
        if profile.vector_kind != "dense":
            raise HybridRetrievalError("dense query requires a dense named vector")
        if profile.dimension != embedding.dimension:
            raise HybridRetrievalError("dense query dimension differs from collection profile")
        hits = self._executor.query_named_dense(
            embedding.values,
            collection_name=collection.collection_name,
            vector_name=embedding.vector_name,
            limit=query.dense_candidate_limit,
            filter_mapping=query.filter.to_qdrant_filter(),
        )
        return _candidates(hits, source="dense")

    def search_sparse(
        self,
        sparse_query: SparseLexicalQuery,
        *,
        query: HybridRetrievalQuery,
        collection: QdrantCollectionProfile,
    ) -> tuple[HybridRetrievalCandidate, ...]:
        profile = collection.vector(sparse_query.vector_name)
        if profile.vector_kind != "sparse":
            raise HybridRetrievalError("sparse query requires a sparse named vector")
        hits = self._executor.query_named_sparse(
            sparse_query.indices,
            sparse_query.weights,
            collection_name=collection.collection_name,
            vector_name=sparse_query.vector_name,
            limit=query.sparse_candidate_limit,
            filter_mapping=query.filter.to_qdrant_filter(),
        )
        return _candidates(hits, source="sparse")


def build_love_qdrant_hybrid_query_adapter(
    executor: NamedQdrantQueryExecutor,
) -> LoveQdrantHybridQueryAdapter:
    return LoveQdrantHybridQueryAdapter(executor)


def _candidates(
    hits: Sequence[QdrantReferenceHitLike],
    *,
    source: str,
) -> tuple[HybridRetrievalCandidate, ...]:
    return tuple(
        HybridRetrievalCandidate(
            schema=HYBRID_CANDIDATE_SCHEMA,
            source=source,
            point_id=hit.point_id,
            sql_ref=hit.sql_ref,
            source_ref=hit.source_ref,
            score=hit.score,
            payload=dict(hit.payload),
        )
        for hit in hits
    )


__all__ = (
    "LOVE_QDRANT_HYBRID_QUERY_ADAPTER_SCHEMA",
    "LoveQdrantHybridQueryAdapter",
    "LoveQdrantHybridQueryAdapterReceipt",
    "NamedQdrantQueryExecutor",
    "QdrantReferenceHitLike",
    "build_love_qdrant_hybrid_query_adapter",
)
