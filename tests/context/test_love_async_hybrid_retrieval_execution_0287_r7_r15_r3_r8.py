from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import context.love_async_hybrid_retrieval_execution_0287 as module
from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    DenseQueryEmbedding,
)
from context.love_async_hybrid_retrieval_execution_0287 import (
    LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA,
    LoveAsyncHybridRetrievalExecutionError,
    execute_love_async_hybrid_retrieval,
)


def _embedding() -> DenseQueryEmbedding:
    return DenseQueryEmbedding(
        schema=DENSE_QUERY_EMBEDDING_SCHEMA,
        query_ref="retrieval-query:love-r8",
        vector_name="dense_e5_v1",
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
        backend_ref="openvino:multilingual-e5-small",
        values=(1.0,) + (0.0,) * 383,
        normalized=True,
    )


class _AsyncEmbedder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def embed_query(self, query_text, *, query_ref, vector_name):
        self.calls.append((query_text, query_ref, vector_name))
        return _embedding()


def _query():
    return SimpleNamespace(
        query_text="relation durable",
        query_ref="retrieval-query:love-r8",
        dense_vector_name="dense_e5_v1",
    )


def test_async_execution_awaits_once_and_delegates_existing_composition(
    monkeypatch,
) -> None:
    embedder = _AsyncEmbedder()
    sentinel = SimpleNamespace(to_mapping=lambda: {"schema": "sentinel"})
    observed = {}

    def fake_execute(query, *, collection, embedder, executor, authority_store):
        observed["query"] = query
        observed["collection"] = collection
        observed["executor"] = executor
        observed["authority_store"] = authority_store
        observed["embedding"] = embedder.embed_query(
            query.query_text,
            query_ref=query.query_ref,
            vector_name=query.dense_vector_name,
        )
        return sentinel

    monkeypatch.setattr(module, "execute_hybrid_retrieval", fake_execute)
    query = _query()
    collection = object()
    executor = object()
    authority_store = object()

    result = asyncio.run(
        execute_love_async_hybrid_retrieval(
            query,
            collection=collection,
            embedder=embedder,
            executor=executor,
            authority_store=authority_store,
        )
    )

    assert embedder.calls == [
        ("relation durable", "retrieval-query:love-r8", "dense_e5_v1")
    ]
    assert observed == {
        "query": query,
        "collection": collection,
        "executor": executor,
        "authority_store": authority_store,
        "embedding": _embedding(),
    }
    assert result.retrieval is sentinel
    assert result.receipt.embedding_dimension == 384
    assert result.receipt.to_mapping()["boundaries"][
        "existing_hybrid_composition_reused"
    ] is True


def test_precomputed_embedding_refuses_another_query(monkeypatch) -> None:
    def fake_execute(query, *, collection, embedder, executor, authority_store):
        return embedder.embed_query(
            "other query",
            query_ref=query.query_ref,
            vector_name=query.dense_vector_name,
        )

    monkeypatch.setattr(module, "execute_hybrid_retrieval", fake_execute)

    with pytest.raises(
        LoveAsyncHybridRetrievalExecutionError,
        match="another query",
    ):
        asyncio.run(
            execute_love_async_hybrid_retrieval(
                _query(),
                collection=object(),
                embedder=_AsyncEmbedder(),
                executor=object(),
                authority_store=object(),
            )
        )


def test_result_mapping_contains_no_raw_embedding() -> None:
    receipt = module.LoveAsyncHybridRetrievalExecutionReceipt(
        schema=LOVE_ASYNC_HYBRID_RETRIEVAL_EXECUTION_SCHEMA,
        query_ref="retrieval-query:love-r8",
        vector_name="dense_e5_v1",
        embedding_dimension=384,
    )

    mapping = receipt.to_mapping()

    assert mapping["embedding_dimension"] == 384
    assert mapping["boundaries"]["raw_vector_serialized"] is False
    assert "values" not in mapping
