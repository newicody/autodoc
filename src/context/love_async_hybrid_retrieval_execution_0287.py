"""Async entry point for the existing hybrid retrieval composition.

The existing r8-r4 composition remains the single authority for collection
profile validation, dense and sparse search, reciprocal-rank fusion and SQL
rehydration. This module only awaits an injected asynchronous dense-query
embedder and delegates the rest of the execution to that existing composition.

It creates no Scheduler, OpenVINO runtime, Qdrant client, SQL store or event
loop. Qdrant and SQL stay behind the ports already defined by r8-r4.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from context.hybrid_retrieval_sql_rehydration_0287 import (
    DenseQueryEmbedding,
    HybridRetrievalQuery,
    HybridRetrievalResult,
    QdrantHybridQueryExecutor,
    SqlAuthorityReader,
    execute_hybrid_retrieval,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile


LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA = (
    "missipy.love.async_hybrid_retrieval_execution.v1"
)


class LoveAsyncHybridRetrievalExecutionError(RuntimeError):
    """Raised when a precomputed embedding is reused for another query."""


class AsyncDenseQueryEmbedder(Protocol):
    """Asynchronous dense-query subset implemented by the E5 adapter."""

    async def embed_query(
        self,
        query_text: str,
        *,
        query_ref: str,
        vector_name: str,
    ) -> DenseQueryEmbedding:
        """Produce one normalized dense query embedding."""


@dataclass(frozen=True, slots=True)
class LoveAsyncHybridRetrievalExecutionReceipt:
    """Serializable evidence for one delegated async execution."""

    schema: str
    query_ref: str
    vector_name: str
    embedding_dimension: int

    def __post_init__(self) -> None:
        if self.schema != LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA:
            raise LoveAsyncHybridRetrievalExecutionError(
                "unsupported async hybrid retrieval execution schema"
            )
        if not self.query_ref.startswith("retrieval-query:"):
            raise LoveAsyncHybridRetrievalExecutionError(
                "query_ref must start with retrieval-query:"
            )
        if not self.vector_name:
            raise LoveAsyncHybridRetrievalExecutionError(
                "vector_name must be non-empty"
            )
        if self.embedding_dimension != 384:
            raise LoveAsyncHybridRetrievalExecutionError(
                "installed E5 embedding dimension must be 384"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "query_ref": self.query_ref,
            "vector_name": self.vector_name,
            "embedding_dimension": self.embedding_dimension,
            "boundaries": {
                "existing_hybrid_composition_reused": True,
                "dense_embedding_awaited": True,
                "second_event_loop_started": False,
                "scheduler_constructed": False,
                "qdrant_client_constructed": False,
                "sql_store_constructed": False,
                "raw_vector_serialized": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LoveAsyncHybridRetrievalExecutionResult:
    """Hybrid result plus non-secret async-delegation evidence."""

    retrieval: HybridRetrievalResult
    receipt: LoveAsyncHybridRetrievalExecutionReceipt

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA,
            "retrieval": self.retrieval.to_mapping(),
            "receipt": self.receipt.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class _PrecomputedDenseQueryEmbedder:
    """Synchronous one-shot bridge consumed by the existing r8-r4 function."""

    query_text: str
    query_ref: str
    vector_name: str
    embedding: DenseQueryEmbedding

    def embed_query(
        self,
        query_text: str,
        *,
        query_ref: str,
        vector_name: str,
    ) -> DenseQueryEmbedding:
        if (
            query_text != self.query_text
            or query_ref != self.query_ref
            or vector_name != self.vector_name
        ):
            raise LoveAsyncHybridRetrievalExecutionError(
                "precomputed embedding cannot be reused for another query"
            )
        return self.embedding


async def execute_love_async_hybrid_retrieval(
    query: HybridRetrievalQuery,
    *,
    collection: QdrantCollectionProfile,
    embedder: AsyncDenseQueryEmbedder,
    executor: QdrantHybridQueryExecutor,
    authority_store: SqlAuthorityReader,
) -> LoveAsyncHybridRetrievalExecutionResult:
    """Await E5 once, then reuse the complete existing hybrid composition."""

    embedding = await embedder.embed_query(
        query.query_text,
        query_ref=query.query_ref,
        vector_name=query.dense_vector_name,
    )
    retrieval = execute_hybrid_retrieval(
        query,
        collection=collection,
        embedder=_PrecomputedDenseQueryEmbedder(
            query_text=query.query_text,
            query_ref=query.query_ref,
            vector_name=query.dense_vector_name,
            embedding=embedding,
        ),
        executor=executor,
        authority_store=authority_store,
    )
    return LoveAsyncHybridRetrievalExecutionResult(
        retrieval=retrieval,
        receipt=LoveAsyncHybridRetrievalExecutionReceipt(
            schema=LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA,
            query_ref=query.query_ref,
            vector_name=query.dense_vector_name,
            embedding_dimension=embedding.dimension,
        ),
    )


__all__ = (
    "LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA",
    "AsyncDenseQueryEmbedder",
    "LoveAsyncHybridRetrievalExecutionError",
    "LoveAsyncHybridRetrievalExecutionReceipt",
    "LoveAsyncHybridRetrievalExecutionResult",
    "execute_love_async_hybrid_retrieval",
)
