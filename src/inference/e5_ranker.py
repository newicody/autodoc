from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .e5_text import E5Text, ensure_e5_text
from .embedding_pipeline import OpenVINOEmbeddingPipelineResult


class E5EmbeddingPipelineLike(Protocol):
    """Sous-ensemble du pipeline embedding utilisé par le ranker local."""

    async def embed_text(self, text: str) -> OpenVINOEmbeddingPipelineResult:
        """Produit un embedding pour un texte déjà préfixé E5."""


@dataclass(frozen=True, slots=True)
class E5Similarity:
    """Score de similarité entre une query et un passage E5."""

    query: E5Text
    passage: E5Text
    score: float
    query_embedding: OpenVINOEmbeddingPipelineResult
    passage_embedding: OpenVINOEmbeddingPipelineResult

    def __post_init__(self) -> None:
        if not self.query.is_query:
            raise ValueError("E5Similarity.query must have role 'query'")
        if not self.passage.is_passage:
            raise ValueError("E5Similarity.passage must have role 'passage'")


@dataclass(frozen=True, slots=True)
class E5RankedPassage:
    """Passage classé par rapport à une query E5."""

    rank: int
    passage: E5Text
    score: float
    embedding: OpenVINOEmbeddingPipelineResult

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("E5RankedPassage.rank must be positive")
        if not self.passage.is_passage:
            raise ValueError("E5RankedPassage.passage must have role 'passage'")


@dataclass(frozen=True, slots=True)
class E5RankedResults:
    """Résultat stable d'un ranking local query -> passages."""

    query: E5Text
    query_embedding: OpenVINOEmbeddingPipelineResult
    passages: tuple[E5RankedPassage, ...]

    def __post_init__(self) -> None:
        if not self.query.is_query:
            raise ValueError("E5RankedResults.query must have role 'query'")
        if len({item.rank for item in self.passages}) != len(self.passages):
            raise ValueError("E5RankedResults.passages ranks must be unique")

    @property
    def best(self) -> E5RankedPassage | None:
        """Meilleur passage, ou None si aucun passage n'a été fourni."""

        return self.passages[0] if self.passages else None


class E5LocalRanker:
    """Mini-ranker local avant Qdrant.

    Le ranker encode une query en `query:` puis des passages en `passage:` et
    trie les passages par produit scalaire. Avec des vecteurs normalisés, ce
    produit scalaire est équivalent à la cosine similarity.
    """

    def __init__(self, pipeline: E5EmbeddingPipelineLike) -> None:
        self._pipeline = pipeline

    async def rank(
        self,
        query: str | E5Text,
        passages: Sequence[str | E5Text],
        *,
        limit: int | None = None,
    ) -> E5RankedResults:
        """Classe des passages par similarité décroissante."""

        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive or None")

        query_text = ensure_e5_text(query, default_role="query")
        if not query_text.is_query:
            raise ValueError("rank query must have role 'query'")

        passage_texts = tuple(ensure_e5_text(item, default_role="passage") for item in passages)
        if any(not item.is_passage for item in passage_texts):
            raise ValueError("rank passages must have role 'passage'")

        query_embedding = await self._pipeline.embed_text(query_text.prefixed)
        scored: list[tuple[float, E5Text, OpenVINOEmbeddingPipelineResult]] = []
        for passage in passage_texts:
            embedding = await self._pipeline.embed_text(passage.prefixed)
            score = dot_product(query_embedding.vector.values, embedding.vector.values)
            scored.append((score, passage, embedding))

        scored.sort(key=lambda item: item[0], reverse=True)
        if limit is not None:
            scored = scored[:limit]

        ranked = tuple(
            E5RankedPassage(rank=index + 1, passage=passage, score=score, embedding=embedding)
            for index, (score, passage, embedding) in enumerate(scored)
        )
        return E5RankedResults(query=query_text, query_embedding=query_embedding, passages=ranked)


def dot_product(left: Sequence[float], right: Sequence[float]) -> float:
    """Produit scalaire entre deux vecteurs de même dimension."""

    left_values = tuple(float(value) for value in left)
    right_values = tuple(float(value) for value in right)
    if not left_values or not right_values:
        raise ValueError("dot_product vectors must not be empty")
    if len(left_values) != len(right_values):
        raise ValueError("dot_product vectors must have the same dimension")
    return sum(a * b for a, b in zip(left_values, right_values, strict=True))
