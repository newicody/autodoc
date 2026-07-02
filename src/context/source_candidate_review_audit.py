from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .source_candidate import SourceCandidateDecision
from .source_candidate_review import SourceCandidateReviewItem, SourceCandidateReviewResult

_REVIEW_AUDIT_SCHEMA = "missipy.source_candidate.review_audit.v1"
_AUDIT_SCHEMA = "missipy.source_candidate.decision_audit.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewAuditPolicy:
    """Politique locale d'enrichissement audit pour une review SourceCandidate."""

    audit_paths: tuple[Path | str, ...] = ()
    audit_dir: Path | str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "audit_paths", tuple(Path(path) for path in self.audit_paths))
        if self.audit_dir is not None:
            object.__setattr__(self, "audit_dir", Path(self.audit_dir))

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "audit_paths": [str(path) for path in self.audit_paths],
            "audit_dir": str(self.audit_dir) if self.audit_dir is not None else None,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateDecisionSummary:
    """Résumé stable de la décision stockée sur une candidate."""

    action: str = ""
    reason: str = ""
    target_context_id: str | None = None
    resulting_status: str = ""

    @classmethod
    def from_decision(
        cls,
        decision: SourceCandidateDecision | None,
    ) -> "SourceCandidateDecisionSummary | None":
        if decision is None:
            return None
        payload = decision.to_json_dict()
        return cls(
            action=str(payload["action"]),
            reason=str(payload["reason"]),
            target_context_id=(
                str(payload["target_context_id"])
                if payload["target_context_id"] is not None
                else None
            ),
            resulting_status=str(payload["resulting_status"]),
        )

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "action": self.action,
            "reason": self.reason,
            "target_context_id": self.target_context_id,
            "resulting_status": self.resulting_status,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateAuditSummary:
    """Résumé stable d'un rapport audit local lu depuis disque."""

    path: Path | str
    action: str
    before_status: str
    after_status: str
    reason: str = ""
    target_context_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "path": str(self.path),
            "action": self.action,
            "before_status": self.before_status,
            "after_status": self.after_status,
            "reason": self.reason,
            "target_context_id": self.target_context_id,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewAuditItem:
    """Projection opérateur enrichie avec décision et audit local."""

    item: SourceCandidateReviewItem
    decision: SourceCandidateDecisionSummary | None = None
    audit: SourceCandidateAuditSummary | None = None

    @property
    def candidate_id(self) -> str:
        return self.item.candidate.candidate_id

    @property
    def audit_present(self) -> bool:
        return self.audit is not None

    def to_json_dict(self) -> dict[str, object | None]:
        payload = self.item.to_json_dict()
        payload["decision_summary"] = (
            self.decision.to_json_dict() if self.decision is not None else None
        )
        payload["audit_present"] = self.audit_present
        payload["audit_summary"] = self.audit.to_json_dict() if self.audit is not None else None
        return payload


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewAuditResult:
    """Résultat de review enrichi par les audits locaux disponibles."""

    review: SourceCandidateReviewResult
    items: tuple[SourceCandidateReviewAuditItem, ...]
    policy: SourceCandidateReviewAuditPolicy
    audit_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            object.__setattr__(self, "items", tuple(self.items))
        if self.audit_count < 0:
            raise ValueError("audit_count must be >= 0")

    @property
    def returned_count(self) -> int:
        return len(self.items)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REVIEW_AUDIT_SCHEMA,
            "review": self.review.to_json_dict(),
            "returned_count": self.returned_count,
            "audit_count": self.audit_count,
            "policy": self.policy.to_json_dict(),
            "items": [item.to_json_dict() for item in self.items],
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate review audit summary",
            f"store: {self.review.store_path}",
            f"returned: {self.returned_count}/{self.review.matched_count} matched ({self.review.snapshot_count} total)",
            f"audits indexed: {self.audit_count}",
        ]
        if not self.items:
            lines.append("No SourceCandidate to review.")
            return "\n".join(lines)
        for item in self.items:
            lines.append(
                f"- {item.candidate_id} [{item.item.candidate.status}] {item.item.candidate.title}"
            )
            if item.decision is not None:
                lines.append(f"  decision: {item.decision.action} -> {item.decision.resulting_status}")
                if item.decision.reason:
                    lines.append(f"  reason: {item.decision.reason}")
                if item.decision.target_context_id:
                    lines.append(f"  target_context_id: {item.decision.target_context_id}")
            if item.audit is not None:
                lines.append(f"  audit: {item.audit.path}")
            if item.item.body_preview:
                lines.append(f"  {item.item.body_preview}")
        return "\n".join(lines)


def enrich_source_candidate_review_with_audit(
    review: SourceCandidateReviewResult,
    policy: SourceCandidateReviewAuditPolicy | None = None,
) -> SourceCandidateReviewAuditResult:
    """Ajoute les résumés de décision et d'audit à une review existante."""
    effective_policy = policy or SourceCandidateReviewAuditPolicy()
    audits = _load_audits(effective_policy)
    items = tuple(
        SourceCandidateReviewAuditItem(
            item=item,
            decision=SourceCandidateDecisionSummary.from_decision(item.candidate.decision),
            audit=audits.get(item.candidate.candidate_id),
        )
        for item in review.items
    )
    return SourceCandidateReviewAuditResult(
        review=review,
        items=items,
        policy=effective_policy,
        audit_count=len(audits),
    )


def _load_audits(
    policy: SourceCandidateReviewAuditPolicy,
) -> dict[str, SourceCandidateAuditSummary]:
    audits: dict[str, SourceCandidateAuditSummary] = {}
    for path in _audit_paths(policy):
        summary = _read_audit(path)
        if summary is None:
            continue
        candidate_id = _read_candidate_id(path)
        if candidate_id is None:
            continue
        audits.setdefault(candidate_id, summary)
    return audits


def _audit_paths(policy: SourceCandidateReviewAuditPolicy) -> tuple[Path, ...]:
    paths = list(Path(path) for path in policy.audit_paths)
    if policy.audit_dir is not None and Path(policy.audit_dir).exists():
        paths.extend(sorted(Path(policy.audit_dir).rglob("*.json")))
    return tuple(sorted(set(paths)))


def _read_candidate_id(path: Path) -> str | None:
    payload = _read_json(path)
    if payload is None:
        return None
    candidate_id = payload.get("candidate_id")
    return candidate_id if isinstance(candidate_id, str) and candidate_id else None


def _read_audit(path: Path) -> SourceCandidateAuditSummary | None:
    payload = _read_json(path)
    if payload is None or payload.get("schema") != _AUDIT_SCHEMA:
        return None
    return SourceCandidateAuditSummary(
        path=path,
        action=_string(payload, "action"),
        before_status=_string(payload, "before_status"),
        after_status=_string(payload, "after_status"),
        reason=_string(payload, "reason"),
        target_context_id=_optional_string(payload, "target_context_id"),
    )


def _read_json(path: Path) -> Mapping[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, Mapping) else None


def _string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key, "")
    return value if isinstance(value, str) else str(value)


def _optional_string(payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)
