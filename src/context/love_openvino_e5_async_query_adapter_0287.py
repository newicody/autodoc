"""Async OpenVINO E5 query adapter for the installed love runtime.

This module adapts the existing asynchronous multilingual-e5-small embedding
pipeline to the dense-query contract used by hybrid retrieval. It does not
construct OpenVINO, a Scheduler, Qdrant or PostgreSQL. The already-built
pipeline is injected by the future tool-bounded runtime composer.

The adapter intentionally exposes ``async embed_query``. It awaits the injected
pipeline directly and therefore cannot create a nested event loop inside the
Scheduler-owned execution path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from context.hybrid_retrieval_sql_rehydration_0287 import (
    DENSE_QUERY_EMBEDDING_SCHEMA,
    DenseQueryEmbedding,
)


LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA = (
    "missipy.love.openvino_e5_async_query_adapter.v1"
)


class LoveOpenVinoE5AsyncQueryAdapterError(RuntimeError):
    """Raised when the injected E5 pipeline violates the locked contract."""


@runtime_checkable
class AsyncEmbeddingPipeline(Protocol):
    """Narrow asynchronous subset of the existing embedding pipeline."""

    async def embed_text(self, text: str) -> Any:
        """Return one embedding-pipeline result for the supplied text."""


@dataclass(frozen=True, slots=True)
class LoveOpenVinoE5AsyncQueryAdapterSettings:
    """Immutable identity and prefix settings for the installed E5 adapter."""

    schema: str
    model_ref: str
    model_revision: str
    backend_ref: str
    query_prefix: str = "query:"
    dimension: int = 384

    def __post_init__(self) -> None:
        if self.schema != LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "unsupported OpenVINO E5 async query-adapter schema"
            )
        for name in ("model_ref", "backend_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or ":" not in value:
                raise LoveOpenVinoE5AsyncQueryAdapterError(
                    f"{name} must be a typed reference"
                )
        if not isinstance(self.model_revision, str) or not self.model_revision:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "model_revision must be a non-empty string"
            )
        if not isinstance(self.query_prefix, str) or not self.query_prefix.strip():
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "query_prefix must be a non-empty string"
            )
        if self.dimension != 384:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "installed multilingual-e5-small dimension must be 384"
            )


@dataclass(frozen=True, slots=True)
class LoveOpenVinoE5AsyncQueryAdapterReceipt:
    """Serializable evidence for one adapter construction."""

    schema: str
    model_ref: str
    model_revision: str
    backend_ref: str
    query_prefix: str
    dimension: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "backend_ref": self.backend_ref,
            "query_prefix": self.query_prefix,
            "dimension": self.dimension,
            "boundaries": {
                "existing_embedding_pipeline_reused": True,
                "asyncio_run_used": False,
                "scheduler_constructed": False,
                "openvino_runtime_constructed": False,
                "qdrant_called": False,
                "postgresql_called": False,
                "raw_vector_serialized": False,
            },
        }


class LoveOpenVinoE5AsyncQueryEmbedder:
    """Convert one existing async E5 pipeline result to DenseQueryEmbedding."""

    def __init__(
        self,
        *,
        pipeline: AsyncEmbeddingPipeline,
        settings: LoveOpenVinoE5AsyncQueryAdapterSettings,
    ) -> None:
        if not isinstance(pipeline, AsyncEmbeddingPipeline):
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "pipeline must expose async embed_text()"
            )
        self._pipeline = pipeline
        self._settings = settings
        self._receipt = LoveOpenVinoE5AsyncQueryAdapterReceipt(
            schema=settings.schema,
            model_ref=settings.model_ref,
            model_revision=settings.model_revision,
            backend_ref=settings.backend_ref,
            query_prefix=settings.query_prefix,
            dimension=settings.dimension,
        )

    @property
    def receipt(self) -> LoveOpenVinoE5AsyncQueryAdapterReceipt:
        return self._receipt

    async def embed_query(
        self,
        query_text: str,
        *,
        query_ref: str,
        vector_name: str,
    ) -> DenseQueryEmbedding:
        """Embed a query without creating or nesting an event loop."""

        text = _prefixed_query(query_text, self._settings.query_prefix)
        result = await self._pipeline.embed_text(text)
        vector = getattr(result, "vector", None)
        if vector is None:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "embedding pipeline result must expose vector"
            )
        values = tuple(getattr(vector, "values", ()))
        dimension = getattr(vector, "dimension", len(values))
        normalized = getattr(vector, "normalized", False)
        if dimension != self._settings.dimension or len(values) != dimension:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "E5 query vector dimension differs from configured dimension"
            )
        if normalized is not True:
            raise LoveOpenVinoE5AsyncQueryAdapterError(
                "E5 query vector must be normalized"
            )
        return DenseQueryEmbedding(
            schema=DENSE_QUERY_EMBEDDING_SCHEMA,
            query_ref=query_ref,
            vector_name=vector_name,
            model_ref=self._settings.model_ref,
            model_revision=self._settings.model_revision,
            backend_ref=self._settings.backend_ref,
            values=values,
            normalized=True,
        )


def build_love_openvino_e5_async_query_embedder(
    *,
    pipeline: AsyncEmbeddingPipeline,
    settings: LoveOpenVinoE5AsyncQueryAdapterSettings,
) -> LoveOpenVinoE5AsyncQueryEmbedder:
    """Build the narrow adapter around an already-composed E5 pipeline."""

    return LoveOpenVinoE5AsyncQueryEmbedder(
        pipeline=pipeline,
        settings=settings,
    )


def _prefixed_query(query_text: str, query_prefix: str) -> str:
    if not isinstance(query_text, str) or not query_text.strip():
        raise LoveOpenVinoE5AsyncQueryAdapterError(
            "query_text must be a non-empty string"
        )
    prefix = query_prefix.strip()
    text = query_text.strip()
    if text == prefix or text.startswith(prefix + " "):
        return text
    return f"{prefix} {text}"


__all__ = (
    "LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA",
    "AsyncEmbeddingPipeline",
    "LoveOpenVinoE5AsyncQueryAdapterError",
    "LoveOpenVinoE5AsyncQueryAdapterReceipt",
    "LoveOpenVinoE5AsyncQueryAdapterSettings",
    "LoveOpenVinoE5AsyncQueryEmbedder",
    "build_love_openvino_e5_async_query_embedder",
)
