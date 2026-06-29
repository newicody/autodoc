from __future__ import annotations

import json
from contextlib import suppress
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

from .e5_ranker import dot_product
from .e5_text import E5Text, ensure_e5_text
from .embedding_pipeline import OpenVINOEmbeddingPipelineResult


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


class E5CorpusPipelineLike(Protocol):
    """Sous-ensemble du pipeline embedding nécessaire au corpus local."""

    async def embed_text(self, text: str) -> OpenVINOEmbeddingPipelineResult:
        """Produit un embedding pour un texte déjà préfixé E5."""


@dataclass(frozen=True, slots=True)
class E5CorpusDocument:
    """Document/passage local à indexer avec E5."""

    id: str
    text: E5Text
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("E5CorpusDocument.id must not be empty")
        if not self.text.is_passage:
            raise ValueError("E5CorpusDocument.text must have role 'passage'")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @classmethod
    def from_text(
        cls,
        text: str | E5Text,
        *,
        id: str | None = None,
        index: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> E5CorpusDocument:
        """Construit un document passage avec identifiant stable."""

        e5_text = ensure_e5_text(text, default_role="passage")
        if not e5_text.is_passage:
            raise ValueError("E5CorpusDocument.from_text expects a passage")
        document_id = id or make_corpus_document_id(e5_text.prefixed, index=index)
        return cls(id=document_id, text=e5_text, metadata=metadata or {})


@dataclass(frozen=True, slots=True)
class E5CorpusEmbedding:
    """Passage local avec vecteur embedding persistant."""

    id: str
    text: str
    prefixed_text: str
    vector: tuple[float, ...]
    dimension: int
    normalized: bool
    l2_norm: float
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("E5CorpusEmbedding.id must not be empty")
        if not self.text:
            raise ValueError("E5CorpusEmbedding.text must not be empty")
        if not self.prefixed_text.startswith("passage:"):
            raise ValueError("E5CorpusEmbedding.prefixed_text must start with 'passage:'")
        vector = tuple(float(value) for value in self.vector)
        if not vector:
            raise ValueError("E5CorpusEmbedding.vector must not be empty")
        if self.dimension != len(vector):
            raise ValueError("E5CorpusEmbedding.dimension must match vector length")
        object.__setattr__(self, "vector", vector)
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @classmethod
    def from_pipeline_result(
        cls,
        document: E5CorpusDocument,
        result: OpenVINOEmbeddingPipelineResult,
    ) -> E5CorpusEmbedding:
        """Projette un résultat pipeline en embedding de corpus."""

        return cls(
            id=document.id,
            text=document.text.content,
            prefixed_text=document.text.prefixed,
            vector=tuple(float(value) for value in result.vector.values),
            dimension=result.vector.dimension,
            normalized=result.vector.normalized,
            l2_norm=result.vector.l2_norm,
            metadata=document.metadata,
        )

    def to_json_dict(self) -> dict[str, Any]:
        """Convertit l'embedding vers JSON stable."""

        return {
            "id": self.id,
            "text": self.text,
            "prefixed_text": self.prefixed_text,
            "vector": list(self.vector),
            "dimension": self.dimension,
            "normalized": self.normalized,
            "l2_norm": self.l2_norm,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> E5CorpusEmbedding:
        """Reconstruit un embedding depuis JSON."""

        return cls(
            id=str(data["id"]),
            text=str(data["text"]),
            prefixed_text=str(data["prefixed_text"]),
            vector=tuple(float(value) for value in data["vector"]),
            dimension=int(data["dimension"]),
            normalized=bool(data["normalized"]),
            l2_norm=float(data["l2_norm"]),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class E5CorpusIndex:
    """Index local immuable de passages E5 déjà vectorisés."""

    model: str
    backend: str
    tokenizer: str
    dimension: int
    embeddings: tuple[E5CorpusEmbedding, ...]
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)
    schema: str = "missipy.e5.corpus.v1"

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("E5CorpusIndex.model must not be empty")
        if not self.backend:
            raise ValueError("E5CorpusIndex.backend must not be empty")
        if not self.tokenizer:
            raise ValueError("E5CorpusIndex.tokenizer must not be empty")
        if self.dimension <= 0:
            raise ValueError("E5CorpusIndex.dimension must be positive")
        embeddings = tuple(self.embeddings)
        ids = [item.id for item in embeddings]
        if len(set(ids)) != len(ids):
            raise ValueError("E5CorpusIndex.embeddings ids must be unique")
        if any(item.dimension != self.dimension for item in embeddings):
            raise ValueError("E5CorpusIndex.embeddings dimensions must match index dimension")
        object.__setattr__(self, "embeddings", embeddings)
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @property
    def size(self) -> int:
        """Nombre de passages indexés."""

        return len(self.embeddings)

    def to_json_dict(self) -> dict[str, Any]:
        """Convertit l'index vers JSON stable."""

        return {
            "schema": self.schema,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "metadata": dict(self.metadata),
            "embeddings": [item.to_json_dict() for item in self.embeddings],
        }

    @classmethod
    def from_json_dict(cls, data: Mapping[str, Any]) -> E5CorpusIndex:
        """Reconstruit un index depuis JSON."""

        schema = str(data.get("schema", ""))
        if schema != "missipy.e5.corpus.v1":
            raise ValueError(f"unsupported E5 corpus schema: {schema!r}")
        return cls(
            model=str(data["model"]),
            backend=str(data["backend"]),
            tokenizer=str(data["tokenizer"]),
            dimension=int(data["dimension"]),
            metadata=dict(data.get("metadata", {})),
            embeddings=tuple(E5CorpusEmbedding.from_json_dict(item) for item in data["embeddings"]),
        )


@dataclass(frozen=True, slots=True)
class E5CorpusSearchHit:
    """Résultat de recherche dans un corpus local."""

    rank: int
    id: str
    score: float
    text: str
    prefixed_text: str
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("E5CorpusSearchHit.rank must be positive")
        if not self.id:
            raise ValueError("E5CorpusSearchHit.id must not be empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    def to_json_dict(self) -> dict[str, Any]:
        """Convertit le hit vers JSON stable."""

        return {
            "rank": self.rank,
            "id": self.id,
            "score": self.score,
            "text": self.text,
            "prefixed_text": self.prefixed_text,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class E5CorpusSearchResults:
    """Résultat stable d'une recherche locale dans un index E5."""

    query: E5Text
    model: str
    backend: str
    tokenizer: str
    dimension: int
    hits: tuple[E5CorpusSearchHit, ...]

    def __post_init__(self) -> None:
        if not self.query.is_query:
            raise ValueError("E5CorpusSearchResults.query must have role 'query'")
        if len({item.rank for item in self.hits}) != len(self.hits):
            raise ValueError("E5CorpusSearchResults.hits ranks must be unique")

    @property
    def best(self) -> E5CorpusSearchHit | None:
        """Meilleur résultat, ou None si l'index est vide."""

        return self.hits[0] if self.hits else None

    def to_json_dict(self) -> dict[str, Any]:
        """Convertit le résultat de recherche vers JSON stable."""

        return {
            "query": self.query.content,
            "prefixed_query": self.query.prefixed,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "hits": [item.to_json_dict() for item in self.hits],
        }


class E5CorpusBuilder:
    """Construit un index local E5 en calculant chaque passage une seule fois."""

    def __init__(self, pipeline: E5CorpusPipelineLike) -> None:
        self._pipeline = pipeline

    async def build(
        self,
        passages: Sequence[str | E5Text | E5CorpusDocument],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> E5CorpusIndex:
        """Vectorise les passages et renvoie un index local immuable."""

        documents = tuple(_to_document(item, index=index) for index, item in enumerate(passages, start=1))
        embeddings: list[E5CorpusEmbedding] = []
        model = backend = tokenizer = ""
        dimension = 0
        for document in documents:
            result = await self._pipeline.embed_text(document.text.prefixed)
            model = result.model
            backend = result.backend
            tokenizer = result.tokenizer_name
            dimension = result.vector.dimension
            embeddings.append(E5CorpusEmbedding.from_pipeline_result(document, result))

        return E5CorpusIndex(
            model=model or "unknown",
            backend=backend or "unknown",
            tokenizer=tokenizer or "unknown",
            dimension=dimension or 1,
            embeddings=tuple(embeddings),
            metadata=metadata or {},
        )


class E5CorpusSearcher:
    """Recherche locale dans un index E5 déjà vectorisé."""

    def __init__(self, pipeline: E5CorpusPipelineLike) -> None:
        self._pipeline = pipeline

    async def search(
        self,
        query: str | E5Text,
        index: E5CorpusIndex,
        *,
        limit: int | None = None,
    ) -> E5CorpusSearchResults:
        """Encode la query puis classe les embeddings persistés."""

        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive or None")
        query_text = ensure_e5_text(query, default_role="query")
        if not query_text.is_query:
            raise ValueError("search query must have role 'query'")

        query_embedding = await self._pipeline.embed_text(query_text.prefixed)
        scores = [
            (dot_product(query_embedding.vector.values, item.vector), item)
            for item in index.embeddings
        ]
        scores.sort(key=lambda item: item[0], reverse=True)
        if limit is not None:
            scores = scores[:limit]
        hits = tuple(
            E5CorpusSearchHit(
                rank=rank,
                id=item.id,
                score=score,
                text=item.text,
                prefixed_text=item.prefixed_text,
                metadata=item.metadata,
            )
            for rank, (score, item) in enumerate(scores, start=1)
        )
        return E5CorpusSearchResults(
            query=query_text,
            model=index.model,
            backend=index.backend,
            tokenizer=index.tokenizer,
            dimension=index.dimension,
            hits=hits,
        )


class E5CorpusJsonStore:
    """Persistance JSON contrôlée d'un corpus E5 local."""

    def write(self, index: E5CorpusIndex, path: str | Path, *, overwrite: bool = False) -> Path:
        """Écrit un index local dans un fichier JSON.

        Cette méthode conserve le comportement historique direct. Pour les CLI
        de build, préférer ``write_atomic`` afin de ne remplacer l'index final
        qu'après sérialisation et validation complètes.
        """

        target = Path(path)
        _ensure_writable_target(target, overwrite=overwrite)
        target.write_text(_serialize_corpus_index(index), encoding="utf-8")
        return target

    def write_atomic(self, index: E5CorpusIndex, path: str | Path, *, overwrite: bool = False) -> Path:
        """Écrit un index avec remplacement atomique du fichier cible.

        Le contenu est d'abord écrit dans un fichier temporaire situé dans le
        même répertoire que la cible, puis relu via ``read`` pour valider que le
        JSON correspond bien au corpus attendu. La cible n'est remplacée par
        ``Path.replace`` que si cette validation réussit.
        """

        target = Path(path)
        _ensure_writable_target(target, overwrite=overwrite)
        temp = atomic_temp_path(target)
        content = _serialize_corpus_index(index)
        if temp.exists():
            temp.unlink()
        try:
            temp.write_text(content, encoding="utf-8")
            loaded = self.read(temp)
            if loaded.to_json_dict() != index.to_json_dict():
                raise ValueError("atomic E5 corpus validation failed")
            temp.replace(target)
        except Exception:
            with suppress(FileNotFoundError):
                temp.unlink()
            raise
        return target

    def read(self, path: str | Path) -> E5CorpusIndex:
        """Lit un index local depuis un fichier JSON."""

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return E5CorpusIndex.from_json_dict(data)


def atomic_temp_path(path: str | Path) -> Path:
    """Chemin temporaire stable utilisé pour un remplacement atomique."""

    target = Path(path)
    if not target.name:
        raise ValueError("atomic temp path target must have a filename")
    return target.with_name(f".{target.name}.tmp")


def _serialize_corpus_index(index: E5CorpusIndex) -> str:
    return json.dumps(
        index.to_json_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def _ensure_writable_target(target: Path, *, overwrite: bool) -> None:
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    if not target.parent.exists():
        raise FileNotFoundError(target.parent)

def make_corpus_document_id(text: str, *, index: int | None = None) -> str:
    """Identifiant stable et lisible pour un passage."""

    digest = sha256(text.encode("utf-8")).hexdigest()[:12]
    if index is None:
        return f"doc-{digest}"
    if index <= 0:
        raise ValueError("index must be positive")
    return f"doc-{index:06d}-{digest}"


def _to_document(item: str | E5Text | E5CorpusDocument, *, index: int) -> E5CorpusDocument:
    if isinstance(item, E5CorpusDocument):
        return item
    return E5CorpusDocument.from_text(item, index=index)
