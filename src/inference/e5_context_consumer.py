from __future__ import annotations

from dataclasses import dataclass

from .e5_context_bundle import E5ContextBundle, E5ContextBundleItem


@dataclass(frozen=True, slots=True)
class E5ContextConsumptionPolicy:
    """Politique explicite de consommation d'un bundle de contexte E5."""

    max_chars: int = 4000
    max_items: int | None = None
    include_scores: bool = False

    def __post_init__(self) -> None:
        if self.max_chars <= 0:
            raise ValueError("max_chars must be positive")
        if self.max_items is not None and self.max_items <= 0:
            raise ValueError("max_items must be positive or None")


@dataclass(frozen=True, slots=True)
class E5ConsumedContextItem:
    """Item de contexte sélectionné pour un futur consommateur de raisonnement."""

    rank: int
    id: str
    text: str
    score: float | None = None
    source_path: str | None = None
    line_range: str | None = None
    chunk_index: int | None = None

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("E5ConsumedContextItem.rank must be positive")
        if not self.id:
            raise ValueError("E5ConsumedContextItem.id must not be empty")
        if not self.text.strip():
            raise ValueError("E5ConsumedContextItem.text must not be empty")

    def to_json_dict(self) -> dict[str, object | None]:
        """Projection JSON stable."""
        return {
            "rank": self.rank,
            "id": self.id,
            "score": self.score,
            "source_path": self.source_path,
            "line_range": self.line_range,
            "chunk_index": self.chunk_index,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class E5ConsumedContext:
    """Résultat stable de préparation d'un bundle E5 pour un futur consommateur."""

    query: str
    prefixed_query: str
    max_chars: int
    used_chars: int
    available_item_count: int
    selected_items: tuple[E5ConsumedContextItem, ...]
    skipped_item_count: int = 0

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("E5ConsumedContext.query must not be empty")
        if not self.prefixed_query.startswith("query:"):
            raise ValueError("E5ConsumedContext.prefixed_query must start with 'query:'")
        if self.max_chars <= 0:
            raise ValueError("E5ConsumedContext.max_chars must be positive")
        if self.used_chars < 0:
            raise ValueError("E5ConsumedContext.used_chars must not be negative")
        if self.used_chars > self.max_chars:
            raise ValueError("E5ConsumedContext.used_chars must not exceed max_chars")
        if self.available_item_count < 0:
            raise ValueError("E5ConsumedContext.available_item_count must not be negative")
        if self.skipped_item_count < 0:
            raise ValueError("E5ConsumedContext.skipped_item_count must not be negative")
        if len({item.rank for item in self.selected_items}) != len(self.selected_items):
            raise ValueError("E5ConsumedContext.selected_items ranks must be unique")

    @property
    def selected_item_count(self) -> int:
        """Nombre d'items retenus dans le budget."""
        return len(self.selected_items)

    @property
    def context_text(self) -> str:
        """Texte de contexte déterministe destiné au futur consommateur."""
        return "\n\n".join(item.text for item in self.selected_items)

    def to_json_dict(self) -> dict[str, object]:
        """Projection JSON stable."""
        return {
            "query": self.query,
            "prefixed_query": self.prefixed_query,
            "max_chars": self.max_chars,
            "used_chars": self.used_chars,
            "available_item_count": self.available_item_count,
            "selected_item_count": self.selected_item_count,
            "skipped_item_count": self.skipped_item_count,
            "context_text": self.context_text,
            "items": [item.to_json_dict() for item in self.selected_items],
        }

    def to_text(self) -> str:
        """Projection texte stable pour inspection humaine."""
        lines = [
            f"query: {self.query}",
            f"prefixed_query: {self.prefixed_query}",
            f"context_budget_chars: {self.used_chars}/{self.max_chars}",
            f"available_item_count: {self.available_item_count}",
            f"selected_item_count: {self.selected_item_count}",
            f"skipped_item_count: {self.skipped_item_count}",
        ]
        if self.context_text:
            lines.extend(("", self.context_text))
        return "\n".join(lines)


def consume_e5_context_bundle(
    bundle: E5ContextBundle,
    policy: E5ContextConsumptionPolicy | None = None,
) -> E5ConsumedContext:
    """Prépare un contexte déterministe depuis un bundle E5 sans effet de bord."""
    effective = policy or E5ContextConsumptionPolicy()
    candidates = bundle.items
    if effective.max_items is not None:
        candidates = candidates[: effective.max_items]

    selected: list[E5ConsumedContextItem] = []
    text_parts: list[str] = []
    used_chars = 0
    separator_chars = 2
    skipped_due_budget = 0

    for item in candidates:
        consumed = _consume_item(item, include_scores=effective.include_scores)
        extra_chars = len(consumed.text)
        if text_parts:
            extra_chars += separator_chars
        if used_chars + extra_chars > effective.max_chars:
            skipped_due_budget = len(candidates) - len(selected)
            break
        selected.append(consumed)
        text_parts.append(consumed.text)
        used_chars += extra_chars

    skipped_due_limit = 0
    if effective.max_items is not None and len(bundle.items) > effective.max_items:
        skipped_due_limit = len(bundle.items) - effective.max_items

    return E5ConsumedContext(
        query=bundle.query,
        prefixed_query=bundle.prefixed_query,
        max_chars=effective.max_chars,
        used_chars=used_chars,
        available_item_count=bundle.item_count,
        selected_items=tuple(selected),
        skipped_item_count=skipped_due_limit + skipped_due_budget,
    )


def _consume_item(item: E5ContextBundleItem, *, include_scores: bool) -> E5ConsumedContextItem:
    text = _format_item_text(item, include_scores=include_scores)
    return E5ConsumedContextItem(
        rank=item.rank,
        id=item.id,
        score=item.score,
        source_path=item.source_path,
        line_range=item.line_range,
        chunk_index=item.chunk_index,
        text=text,
    )


def _format_item_text(item: E5ContextBundleItem, *, include_scores: bool) -> str:
    title = f"[{item.rank}]"
    if item.source_path is not None:
        title += f" {item.source_path}"
    else:
        title += f" {item.id}"
    if item.line_range is not None:
        title += f":{item.line_range}"
    lines = [title]
    if include_scores and item.score is not None:
        lines.append(f"score: {item.score:.8f}")
    lines.append(item.excerpt)
    return "\n".join(lines)
