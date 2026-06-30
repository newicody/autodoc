from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .e5_search_report import E5SearchReport


@dataclass(frozen=True, slots=True)
class E5ContextBundleItem:
    """Élément de contexte stable extrait d'un hit de recherche E5."""

    rank: int
    id: str
    excerpt: str
    score: float | None = None
    source_path: str | None = None
    line_range: str | None = None
    chunk_index: int | None = None

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("E5ContextBundleItem.rank must be positive")
        if not self.id:
            raise ValueError("E5ContextBundleItem.id must not be empty")
        if not self.excerpt.strip():
            raise ValueError("E5ContextBundleItem.excerpt must not be empty")

    def to_json_dict(self) -> dict[str, object | None]:
        """Projection JSON stable."""
        return {
            "rank": self.rank,
            "id": self.id,
            "score": self.score,
            "source_path": self.source_path,
            "line_range": self.line_range,
            "chunk_index": self.chunk_index,
            "excerpt": self.excerpt,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Projection texte courte pour injection future dans un contexte."""
        title = f"[{self.rank}]"
        if self.source_path is not None:
            title += f" {self.source_path}"
        if self.line_range is not None:
            title += f":{self.line_range}"
        lines = [title, self.excerpt]
        return tuple(lines)


@dataclass(frozen=True, slots=True)
class E5ContextBundle:
    """Bundle de contexte E5 prêt pour un futur composant de réponse."""

    query: str
    prefixed_query: str
    index: str
    model: str
    backend: str
    tokenizer: str
    dimension: int
    items: tuple[E5ContextBundleItem, ...]

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("E5ContextBundle.query must not be empty")
        if not self.prefixed_query.startswith("query:"):
            raise ValueError("E5ContextBundle.prefixed_query must start with 'query:'")
        if not self.index:
            raise ValueError("E5ContextBundle.index must not be empty")
        if self.dimension <= 0:
            raise ValueError("E5ContextBundle.dimension must be positive")
        if len({item.rank for item in self.items}) != len(self.items):
            raise ValueError("E5ContextBundle.items ranks must be unique")

    @property
    def item_count(self) -> int:
        """Nombre d'éléments de contexte disponibles."""
        return len(self.items)

    @classmethod
    def from_search_report(cls, report: E5SearchReport) -> E5ContextBundle:
        """Construit un bundle de contexte depuis un rapport de recherche E5."""
        return cls(
            query=report.query,
            prefixed_query=report.prefixed_query,
            index=report.index,
            model=report.model,
            backend=report.backend,
            tokenizer=report.tokenizer,
            dimension=report.dimension,
            items=tuple(_item_from_hit(hit) for hit in report.hits),
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
            "item_count": self.item_count,
            "items": [item.to_json_dict() for item in self.items],
        }

    def to_text(self) -> str:
        """Projection texte compacte pour inspection humaine."""
        lines = [
            f"query: {self.query}",
            f"prefixed_query: {self.prefixed_query}",
            f"index: {self.index}",
            f"context_item_count: {self.item_count}",
        ]
        for item in self.items:
            lines.append("")
            lines.extend(item.to_text_lines())
        return "\n".join(lines)


def _item_from_hit(hit: Any) -> E5ContextBundleItem:
    source = getattr(hit, "source")
    return E5ContextBundleItem(
        rank=int(getattr(hit, "rank")),
        id=str(getattr(hit, "id")),
        score=float(getattr(hit, "score")),
        source_path=getattr(source, "source_path"),
        line_range=getattr(source, "line_range"),
        chunk_index=getattr(source, "chunk_index"),
        excerpt=str(getattr(hit, "excerpt")),
    )
