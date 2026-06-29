from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .e5_corpus import (
    E5CorpusDocument,
    E5CorpusEmbedding,
    E5CorpusIndex,
    E5CorpusPipelineLike,
)
from .e5_text import E5Text
from .embedding_pipeline import OpenVINOEmbeddingPipelineResult


@dataclass(frozen=True, slots=True)
class E5IncrementalBuildStats:
    """Statistiques déterministes d'une reconstruction incrémentale."""

    total_count: int
    reused_count: int
    embedded_count: int
    removed_count: int

    def __post_init__(self) -> None:
        if self.total_count < 0:
            raise ValueError("E5IncrementalBuildStats.total_count must be zero or positive")
        if self.reused_count < 0:
            raise ValueError("E5IncrementalBuildStats.reused_count must be zero or positive")
        if self.embedded_count < 0:
            raise ValueError("E5IncrementalBuildStats.embedded_count must be zero or positive")
        if self.removed_count < 0:
            raise ValueError("E5IncrementalBuildStats.removed_count must be zero or positive")
        if self.reused_count + self.embedded_count != self.total_count:
            raise ValueError("E5IncrementalBuildStats reused+embedded must match total")

    def to_json_dict(self) -> dict[str, int]:
        """Projection JSON stable."""

        return {
            "total_count": self.total_count,
            "reused_count": self.reused_count,
            "embedded_count": self.embedded_count,
            "removed_count": self.removed_count,
        }


@dataclass(frozen=True, slots=True)
class E5IncrementalBuildResult:
    """Résultat immuable d'une reconstruction incrémentale du corpus."""

    index: E5CorpusIndex
    stats: E5IncrementalBuildStats


class E5IncrementalCorpusBuilder:
    """Reconstruit un corpus E5 en réutilisant les embeddings inchangés.

    Le builder ne compare pas les timestamps. Il compare une empreinte stable
    calculée depuis l'identifiant du document et son texte E5 préfixé. Cela
    garde le comportement déterministe et compatible avec les snapshots ZFS/Git.
    """

    def __init__(self, pipeline: E5CorpusPipelineLike) -> None:
        self._pipeline = pipeline

    async def build(
        self,
        passages: Sequence[str | E5Text | E5CorpusDocument],
        *,
        previous_index: E5CorpusIndex | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> E5IncrementalBuildResult:
        """Construit un index en recalculant seulement les documents changés."""

        documents = tuple(_to_document(item, index=index) for index, item in enumerate(passages, start=1))
        previous_by_id = {item.id: item for item in previous_index.embeddings} if previous_index is not None else {}

        embeddings: list[E5CorpusEmbedding] = []
        reused_count = 0
        embedded_count = 0
        model = previous_index.model if previous_index is not None else ""
        backend = previous_index.backend if previous_index is not None else ""
        tokenizer = previous_index.tokenizer if previous_index is not None else ""
        dimension = previous_index.dimension if previous_index is not None else 0

        for document in documents:
            previous = previous_by_id.get(document.id)
            if previous is not None and embedding_matches_document(previous, document):
                embeddings.append(reuse_embedding(previous, document))
                reused_count += 1
                continue

            result = await self._pipeline.embed_text(document.text.prefixed)
            model = result.model
            backend = result.backend
            tokenizer = result.tokenizer_name
            dimension = result.vector.dimension
            embeddings.append(embedding_from_pipeline_result_with_hash(document, result))
            embedded_count += 1

        new_ids = {document.id for document in documents}
        removed_count = sum(1 for item in previous_by_id if item not in new_ids)
        index = E5CorpusIndex(
            model=model or "unknown",
            backend=backend or "unknown",
            tokenizer=tokenizer or "unknown",
            dimension=dimension or 1,
            embeddings=tuple(embeddings),
            metadata={
                **dict(metadata or {}),
                "incremental": True,
                "incremental_stats": E5IncrementalBuildStats(
                    total_count=len(embeddings),
                    reused_count=reused_count,
                    embedded_count=embedded_count,
                    removed_count=removed_count,
                ).to_json_dict(),
            },
        )
        return E5IncrementalBuildResult(
            index=index,
            stats=E5IncrementalBuildStats(
                total_count=len(embeddings),
                reused_count=reused_count,
                embedded_count=embedded_count,
                removed_count=removed_count,
            ),
        )


def make_e5_document_hash(document: E5CorpusDocument) -> str:
    """Empreinte stable d'un document E5 indexable."""

    payload = f"{document.id}\0{document.text.prefixed}".encode("utf-8")
    return sha256(payload).hexdigest()


def embedding_matches_document(embedding: E5CorpusEmbedding, document: E5CorpusDocument) -> bool:
    """Vérifie si un embedding persistant correspond encore au document."""

    if embedding.id != document.id:
        return False
    if embedding.prefixed_text != document.text.prefixed:
        return False
    stored_hash = embedding.metadata.get("document_hash")
    if stored_hash is None:
        # Compatibilité avec les index créés avant la Phase 3.15.
        return True
    return str(stored_hash) == make_e5_document_hash(document)


def reuse_embedding(embedding: E5CorpusEmbedding, document: E5CorpusDocument) -> E5CorpusEmbedding:
    """Réutilise un vecteur existant avec les métadonnées source à jour."""

    metadata = {
        **dict(document.metadata),
        "document_hash": make_e5_document_hash(document),
        "embedding_reused": True,
    }
    return E5CorpusEmbedding(
        id=document.id,
        text=document.text.content,
        prefixed_text=document.text.prefixed,
        vector=embedding.vector,
        dimension=embedding.dimension,
        normalized=embedding.normalized,
        l2_norm=embedding.l2_norm,
        metadata=metadata,
    )


def embedding_from_pipeline_result_with_hash(
    document: E5CorpusDocument,
    result: OpenVINOEmbeddingPipelineResult,
) -> E5CorpusEmbedding:
    """Projette un résultat pipeline en embedding avec empreinte document."""

    metadata = {
        **dict(document.metadata),
        "document_hash": make_e5_document_hash(document),
        "embedding_reused": False,
    }
    return E5CorpusEmbedding(
        id=document.id,
        text=document.text.content,
        prefixed_text=document.text.prefixed,
        vector=tuple(float(value) for value in result.vector.values),
        dimension=result.vector.dimension,
        normalized=result.vector.normalized,
        l2_norm=result.vector.l2_norm,
        metadata=metadata,
    )


def _to_document(item: str | E5Text | E5CorpusDocument, *, index: int) -> E5CorpusDocument:
    if isinstance(item, E5CorpusDocument):
        return item
    return E5CorpusDocument.from_text(item, index=index)
