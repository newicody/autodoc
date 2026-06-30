from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .e5_corpus import E5CorpusIndex, E5CorpusPipelineLike, E5CorpusSearcher


@dataclass(frozen=True, slots=True)
class E5SearchValidationQueryResult:
    """Résultat stable d'une requête de validation E5 locale."""

    query: str
    hit_count: int
    best_score: float | None = None
    min_score: float | None = None

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("E5SearchValidationQueryResult.query must not be empty")
        if self.hit_count < 0:
            raise ValueError("E5SearchValidationQueryResult.hit_count must not be negative")
        if self.min_score is not None and not -1.0 <= self.min_score <= 1.0:
            raise ValueError("E5SearchValidationQueryResult.min_score must be between -1.0 and 1.0")

    @property
    def passed(self) -> bool:
        """Indique si la requête a produit au moins un résultat utile."""
        return self.hit_count > 0

    def to_json_dict(self) -> dict[str, object | None]:
        """Convertit le résultat vers JSON stable."""
        return {
            "query": self.query,
            "hit_count": self.hit_count,
            "best_score": self.best_score,
            "min_score": self.min_score,
            "passed": self.passed,
        }

    def to_text_lines(self) -> tuple[str, ...]:
        """Produit un bloc texte compact pour les rapports CLI."""
        lines = [
            f"query: {self.query}",
            f"hit_count: {self.hit_count}",
            f"passed: {str(self.passed)}",
        ]
        if self.min_score is not None:
            lines.append(f"min_score: {self.min_score:.8f}")
        if self.best_score is not None:
            lines.append(f"best_score: {self.best_score:.8f}")
        return tuple(lines)


async def validate_e5_search_queries(
    pipeline: E5CorpusPipelineLike,
    index: E5CorpusIndex,
    queries: Sequence[str],
    *,
    limit: int = 1,
    min_score: float | None = None,
) -> tuple[E5SearchValidationQueryResult, ...]:
    """Valide plusieurs requêtes sur un corpus local déjà construit."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if min_score is not None and not -1.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between -1.0 and 1.0 or None")

    normalized_queries = tuple(query.strip() for query in queries if query.strip())
    searcher = E5CorpusSearcher(pipeline)
    results: list[E5SearchValidationQueryResult] = []
    for query in normalized_queries:
        search_results = await searcher.search(query, index, limit=limit, min_score=min_score)
        best_score = search_results.best.score if search_results.best is not None else None
        results.append(
            E5SearchValidationQueryResult(
                query=search_results.query.content,
                hit_count=len(search_results.hits),
                best_score=best_score,
                min_score=min_score,
            )
        )
    return tuple(results)
