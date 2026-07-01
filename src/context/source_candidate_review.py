
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .source_candidate import (
    SourceCandidate,
    allowed_source_candidate_decisions,
    allowed_source_candidate_statuses,
)
from .source_candidate_store import SourceCandidateStorePolicy, load_source_candidate_store

_REVIEW_SCHEMA = "missipy.source_candidate.review.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewPolicy:
    """Politique locale de projection opérateur SourceCandidate.

    La review est une lecture/projection déterministe du store local. Elle ne prend
    aucune décision automatique, ne contacte pas GitHub et n'écrit pas dans le store.
    """

    include_terminal: bool = False
    status_filter: tuple[str, ...] = ()
    limit: int = 50
    body_preview_chars: int = 160

    def __post_init__(self) -> None:
        if not isinstance(self.status_filter, tuple):
            object.__setattr__(self, "status_filter", tuple(self.status_filter))
        allowed = set(allowed_source_candidate_statuses())
        for status in self.status_filter:
            if status not in allowed:
                raise ValueError(
                    "status_filter values must be new, analyzed, rejected, archived, promoted or merged"
                )
        if self.limit <= 0:
            raise ValueError("limit must be > 0")
        if self.body_preview_chars <= 0:
            raise ValueError("body_preview_chars must be > 0")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "include_terminal": self.include_terminal,
            "status_filter": list(self.status_filter),
            "limit": self.limit,
            "body_preview_chars": self.body_preview_chars,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewCommand:
    """Commande typée de review SourceCandidate.

    Le chemin d'intégration attendu est Scheduler -> Dispatcher -> Handler -> store
    JSON réel en lecture seule -> résultat observable.
    """

    store_policy: SourceCandidateStorePolicy
    review_policy: SourceCandidateReviewPolicy = SourceCandidateReviewPolicy()


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewItem:
    """Projection stable d'une SourceCandidate pour revue opérateur."""

    candidate: SourceCandidate
    body_preview: str
    decision_options: tuple[str, ...] = field(default_factory=allowed_source_candidate_decisions)

    def __post_init__(self) -> None:
        if not isinstance(self.decision_options, tuple):
            object.__setattr__(self, "decision_options", tuple(self.decision_options))

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "candidate_id": self.candidate.candidate_id,
            "title": self.candidate.title,
            "status": self.candidate.status,
            "terminal": self.candidate.terminal,
            "actionable": self.candidate.actionable,
            "origin": self.candidate.origin.to_json_dict(),
            "labels": list(self.candidate.labels),
            "metadata": dict(self.candidate.metadata),
            "body_preview": self.body_preview,
            "decision_options": list(self.decision_options),
            "candidate": self.candidate.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewResult:
    """Résultat immuable, observable et sérialisable d'une review locale."""

    store_path: Path | str
    snapshot_count: int
    matched_count: int
    items: tuple[SourceCandidateReviewItem, ...]
    policy: SourceCandidateReviewPolicy

    def __post_init__(self) -> None:
        object.__setattr__(self, "store_path", Path(self.store_path))
        if self.snapshot_count < 0:
            raise ValueError("snapshot_count must be >= 0")
        if self.matched_count < 0:
            raise ValueError("matched_count must be >= 0")
        if not isinstance(self.items, tuple):
            object.__setattr__(self, "items", tuple(self.items))

    @property
    def returned_count(self) -> int:
        return len(self.items)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(item.candidate.candidate_id for item in self.items)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REVIEW_SCHEMA,
            "store_path": str(self.store_path),
            "snapshot_count": self.snapshot_count,
            "matched_count": self.matched_count,
            "returned_count": self.returned_count,
            "candidate_ids": list(self.candidate_ids),
            "policy": self.policy.to_json_dict(),
            "items": [item.to_json_dict() for item in self.items],
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate review",
            f"store: {self.store_path}",
            f"returned: {self.returned_count}/{self.matched_count} matched ({self.snapshot_count} total)",
        ]
        if not self.items:
            lines.append("No SourceCandidate to review.")
            return "\n".join(lines)
        for item in self.items:
            lines.append(
                f"- {item.candidate.candidate_id} [{item.candidate.status}] {item.candidate.title}"
            )
            if item.body_preview:
                lines.append(f"  {item.body_preview}")
        return "\n".join(lines)


def run_source_candidate_review(command: SourceCandidateReviewCommand) -> SourceCandidateReviewResult:
    """Lit le store SourceCandidate réel et produit une file de revue locale."""

    snapshot = load_source_candidate_store(command.store_policy)
    filtered = _filter_candidates(snapshot.candidates, command.review_policy)
    limited = filtered[: command.review_policy.limit]
    items = tuple(
        SourceCandidateReviewItem(
            candidate=candidate,
            body_preview=_preview(candidate.body, command.review_policy.body_preview_chars),
        )
        for candidate in limited
    )
    return SourceCandidateReviewResult(
        store_path=command.store_policy.path,
        snapshot_count=snapshot.candidate_count,
        matched_count=len(filtered),
        items=items,
        policy=command.review_policy,
    )


def _filter_candidates(
    candidates: Sequence[SourceCandidate],
    policy: SourceCandidateReviewPolicy,
) -> tuple[SourceCandidate, ...]:
    selected = []
    status_filter = set(policy.status_filter)
    for candidate in candidates:
        if not policy.include_terminal and candidate.terminal:
            continue
        if status_filter and candidate.status not in status_filter:
            continue
        selected.append(candidate)
    return tuple(sorted(selected, key=lambda candidate: candidate.candidate_id))


def _preview(body: str, max_chars: int) -> str:
    if len(body) <= max_chars:
        return body
    if max_chars == 1:
        return "…"
    return body[: max_chars - 1] + "…"
