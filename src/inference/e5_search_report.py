from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .e5_corpus import E5CorpusSearchHit, E5CorpusSearchResults


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class E5SearchReportConfig:
    """Configuration de rendu d'un résultat de recherche E5 local."""

    excerpt_chars: int = 280
    include_full_text: bool = False

    def __post_init__(self) -> None:
        if self.excerpt_chars <= 0:
            raise ValueError("E5SearchReportConfig.excerpt_chars must be positive")


@dataclass(frozen=True, slots=True)
class E5SearchSourceContext:
    """Contexte source extrait des métadonnées d'un chunk."""

    source_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    chunk_index: int | None = None
    source_id: str | None = None
    source_extension: str | None = None

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any]) -> E5SearchSourceContext:
        """Construit un contexte source depuis les métadonnées persistées."""

        return cls(
            source_path=_optional_str(metadata.get("source_path")),
            start_line=_optional_positive_int(metadata.get("start_line")),
            end_line=_optional_positive_int(metadata.get("end_line")),
            chunk_index=_optional_positive_int(metadata.get("chunk_index")),
            source_id=_optional_str(metadata.get("source_id")),
            source_extension=_optional_str(metadata.get("source_extension")),
        )

    @property
    def has_source(self) -> bool:
        """True si le hit peut être relié à une source locale."""

        return self.source_path is not None

    @property
    def line_range(self) -> str | None:
        """Plage de lignes lisible, si disponible."""

        if self.start_line is None or self.end_line is None:
            return None
        if self.start_line == self.end_line:
            return str(self.start_line)
        return f"{self.start_line}-{self.end_line}"

    def to_json_dict(self) -> dict[str, object | None]:
        """Projection JSON stable."""

        return {
            "source_path": self.source_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "line_range": self.line_range,
            "chunk_index": self.chunk_index,
            "source_id": self.source_id,
            "source_extension": self.source_extension,
        }

    def to_text(self) -> tuple[str, ...]:
        """Lignes texte lisibles pour une CLI."""

        if not self.has_source:
            return ()
        lines = [f"source: {self.source_path}"]
        if self.line_range is not None:
            lines.append(f"lines: {self.line_range}")
        if self.chunk_index is not None:
            lines.append(f"chunk: {self.chunk_index}")
        return tuple(lines)


@dataclass(frozen=True, slots=True)
class E5SearchReportHit:
    """Hit enrichi pour affichage humain et JSON."""

    rank: int
    id: str
    score: float
    source: E5SearchSourceContext
    excerpt: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("E5SearchReportHit.rank must be positive")
        if not self.id:
            raise ValueError("E5SearchReportHit.id must not be empty")
        if not self.excerpt:
            raise ValueError("E5SearchReportHit.excerpt must not be empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))

    @classmethod
    def from_search_hit(
        cls,
        hit: E5CorpusSearchHit,
        *,
        config: E5SearchReportConfig | None = None,
    ) -> E5SearchReportHit:
        """Construit un hit de rapport depuis un hit brut de corpus."""

        effective = config or E5SearchReportConfig()
        return cls(
            rank=hit.rank,
            id=hit.id,
            score=float(hit.score),
            source=E5SearchSourceContext.from_metadata(hit.metadata),
            excerpt=make_excerpt(hit.text, max_chars=effective.excerpt_chars),
            text=hit.text,
            metadata=hit.metadata,
        )

    def to_json_dict(self, *, include_full_text: bool = False) -> dict[str, object]:
        """Projection JSON stable."""

        data: dict[str, object] = {
            "rank": self.rank,
            "id": self.id,
            "score": self.score,
            "source": self.source.to_json_dict(),
            "excerpt": self.excerpt,
            "metadata": dict(self.metadata),
        }
        if include_full_text:
            data["text"] = self.text
        return data

    def to_text_lines(self, *, include_full_text: bool = False) -> tuple[str, ...]:
        """Projection texte stable et lisible."""

        lines: list[str] = [f"#{self.rank} score={self.score:.8f}", f"id: {self.id}"]
        lines.extend(self.source.to_text())
        lines.append(f"excerpt: {self.excerpt}")
        if include_full_text:
            lines.append(f"text: {self.text}")
        return tuple(lines)


@dataclass(frozen=True, slots=True)
class E5SearchReport:
    """Rapport lisible d'une recherche E5 locale."""

    query: str
    prefixed_query: str
    index: str
    model: str
    backend: str
    tokenizer: str
    dimension: int
    hits: tuple[E5SearchReportHit, ...]
    config: E5SearchReportConfig = field(default_factory=E5SearchReportConfig)

    def __post_init__(self) -> None:
        if not self.query:
            raise ValueError("E5SearchReport.query must not be empty")
        if not self.prefixed_query.startswith("query:"):
            raise ValueError("E5SearchReport.prefixed_query must start with 'query:'")
        if self.dimension <= 0:
            raise ValueError("E5SearchReport.dimension must be positive")
        if len({item.rank for item in self.hits}) != len(self.hits):
            raise ValueError("E5SearchReport.hits ranks must be unique")

    @classmethod
    def from_results(
        cls,
        *,
        query: str,
        prefixed_query: str,
        index: str,
        results: E5CorpusSearchResults,
        config: E5SearchReportConfig | None = None,
    ) -> E5SearchReport:
        """Construit un rapport depuis les résultats bruts."""

        effective = config or E5SearchReportConfig()
        return cls(
            query=query,
            prefixed_query=prefixed_query,
            index=index,
            model=results.model,
            backend=results.backend,
            tokenizer=results.tokenizer,
            dimension=results.dimension,
            hits=tuple(E5SearchReportHit.from_search_hit(hit, config=effective) for hit in results.hits),
            config=effective,
        )

    def to_json_dict(self) -> dict[str, object]:
        """Projection JSON stable."""

        return {
            "query": self.query,
            "prefixed_query": self.prefixed_query,
            "index": self.index,
            "model": self.model,
            "backend": self.backend,
            "tokenizer": self.tokenizer,
            "dimension": self.dimension,
            "hit_count": len(self.hits),
            "hits": [hit.to_json_dict(include_full_text=self.config.include_full_text) for hit in self.hits],
        }

    def to_text(self) -> str:
        """Projection texte stable et lisible."""

        lines = [
            f"query: {self.query}",
            f"prefixed_query: {self.prefixed_query}",
            f"index: {self.index}",
            f"model: {self.model}",
            f"backend: {self.backend}",
            f"tokenizer: {self.tokenizer}",
            f"dimension: {self.dimension}",
            f"hit_count: {len(self.hits)}",
        ]
        for hit in self.hits:
            lines.append("")
            lines.extend(hit.to_text_lines(include_full_text=self.config.include_full_text))
        return "\n".join(lines)


def make_excerpt(text: str, *, max_chars: int = 280) -> str:
    """Produit un extrait mono-ligne stable depuis un chunk."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    normalized = " ".join(text.split())
    if not normalized:
        raise ValueError("text must not be empty")
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 1:
        return "…"
    return normalized[: max_chars - 1].rstrip() + "…"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text or None


def _optional_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number
