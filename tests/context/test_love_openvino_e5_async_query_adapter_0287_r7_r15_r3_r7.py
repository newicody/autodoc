from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from context.love_openvino_e5_async_query_adapter_0287 import (
    LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA,
    LoveOpenVinoE5AsyncQueryAdapterError,
    LoveOpenVinoE5AsyncQueryAdapterSettings,
    build_love_openvino_e5_async_query_embedder,
)


@dataclass(frozen=True)
class _Vector:
    values: tuple[float, ...]
    normalized: bool = True

    @property
    def dimension(self) -> int:
        return len(self.values)


@dataclass(frozen=True)
class _Result:
    vector: _Vector


class _Pipeline:
    def __init__(self, vector: _Vector) -> None:
        self.vector = vector
        self.texts: list[str] = []

    async def embed_text(self, text: str) -> _Result:
        self.texts.append(text)
        return _Result(self.vector)


def _settings() -> LoveOpenVinoE5AsyncQueryAdapterSettings:
    return LoveOpenVinoE5AsyncQueryAdapterSettings(
        schema=LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA,
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
        backend_ref="openvino:multilingual-e5-small",
    )


def _unit_vector() -> tuple[float, ...]:
    return (1.0,) + (0.0,) * 383


def test_adapter_prefixes_query_and_returns_locked_dense_embedding() -> None:
    pipeline = _Pipeline(_Vector(_unit_vector()))
    adapter = build_love_openvino_e5_async_query_embedder(
        pipeline=pipeline,
        settings=_settings(),
    )

    result = asyncio.run(
        adapter.embed_query(
            "relation durable",
            query_ref="retrieval-query:love-1",
            vector_name="dense_e5_v1",
        )
    )

    assert pipeline.texts == ["query: relation durable"]
    assert result.dimension == 384
    assert result.normalized is True
    assert result.model_ref == "model:multilingual-e5-small"
    assert result.backend_ref == "openvino:multilingual-e5-small"
    assert result.to_mapping()["raw_vector_serialized"] is False


def test_adapter_does_not_duplicate_existing_query_prefix() -> None:
    pipeline = _Pipeline(_Vector(_unit_vector()))
    adapter = build_love_openvino_e5_async_query_embedder(
        pipeline=pipeline,
        settings=_settings(),
    )

    asyncio.run(
        adapter.embed_query(
            "query: relation durable",
            query_ref="retrieval-query:love-2",
            vector_name="dense_e5_v1",
        )
    )

    assert pipeline.texts == ["query: relation durable"]


def test_adapter_rejects_wrong_dimension() -> None:
    adapter = build_love_openvino_e5_async_query_embedder(
        pipeline=_Pipeline(_Vector((1.0, 0.0))),
        settings=_settings(),
    )

    with pytest.raises(
        LoveOpenVinoE5AsyncQueryAdapterError,
        match="dimension",
    ):
        asyncio.run(
            adapter.embed_query(
                "relation",
                query_ref="retrieval-query:love-3",
                vector_name="dense_e5_v1",
            )
        )


def test_adapter_rejects_unnormalized_vector() -> None:
    adapter = build_love_openvino_e5_async_query_embedder(
        pipeline=_Pipeline(_Vector(_unit_vector(), normalized=False)),
        settings=_settings(),
    )

    with pytest.raises(
        LoveOpenVinoE5AsyncQueryAdapterError,
        match="normalized",
    ):
        asyncio.run(
            adapter.embed_query(
                "relation",
                query_ref="retrieval-query:love-4",
                vector_name="dense_e5_v1",
            )
        )


def test_receipt_exposes_boundaries_without_vector() -> None:
    adapter = build_love_openvino_e5_async_query_embedder(
        pipeline=_Pipeline(_Vector(_unit_vector())),
        settings=_settings(),
    )

    mapping = adapter.receipt.to_mapping()

    assert mapping["dimension"] == 384
    assert mapping["boundaries"]["asyncio_run_used"] is False
    assert "values" not in mapping
# r7-r1 keeps the runtime source free of forbidden implementation literals.
