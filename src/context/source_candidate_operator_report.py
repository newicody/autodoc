from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .source_candidate_review_audit import (
    SourceCandidateReviewAuditItem,
    SourceCandidateReviewAuditResult,
)

_REPORT_SCHEMA = "missipy.source_candidate.operator_report.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorReportPolicy:
    """Politique locale de projection d'un rapport opérateur SourceCandidate."""

    include_items: bool = True
    max_next_actions: int = 20

    def __post_init__(self) -> None:
        if self.max_next_actions <= 0:
            raise ValueError("max_next_actions must be > 0")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "include_items": self.include_items,
            "max_next_actions": self.max_next_actions,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorReportItem:
    """Ligne stable de rapport opérateur pour une candidate."""

    candidate_id: str
    title: str
    status: str
    actionable: bool
    audit_present: bool
    decision_action: str = ""
    decision_reason: str = ""
    target_context_id: str | None = None
    recommended_next_action: str = ""

    @classmethod
    def from_review_audit_item(
        cls,
        item: SourceCandidateReviewAuditItem,
    ) -> "SourceCandidateOperatorReportItem":
        candidate = item.item.candidate
        decision_action = item.decision.action if item.decision is not None else ""
        decision_reason = item.decision.reason if item.decision is not None else ""
        target_context_id = (
            item.decision.target_context_id if item.decision is not None else None
        )
        return cls(
            candidate_id=candidate.candidate_id,
            title=candidate.title,
            status=candidate.status,
            actionable=candidate.actionable,
            audit_present=item.audit_present,
            decision_action=decision_action,
            decision_reason=decision_reason,
            target_context_id=target_context_id,
            recommended_next_action=_recommended_next_action(item),
        )

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "status": self.status,
            "actionable": self.actionable,
            "audit_present": self.audit_present,
            "decision_action": self.decision_action,
            "decision_reason": self.decision_reason,
            "target_context_id": self.target_context_id,
            "recommended_next_action": self.recommended_next_action,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorReportResult:
    """Rapport opérateur synthétique dérivé de la review enrichie."""

    review_audit: SourceCandidateReviewAuditResult
    policy: SourceCandidateOperatorReportPolicy
    items: tuple[SourceCandidateOperatorReportItem, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            object.__setattr__(self, "items", tuple(self.items))

    @property
    def returned_count(self) -> int:
        return len(self.items)

    @property
    def actionable_count(self) -> int:
        return sum(1 for item in self.items if item.actionable)

    @property
    def terminal_count(self) -> int:
        return self.returned_count - self.actionable_count

    @property
    def audit_present_count(self) -> int:
        return sum(1 for item in self.items if item.audit_present)

    @property
    def status_counts(self) -> dict[str, int]:
        return dict(sorted(Counter(item.status for item in self.items).items()))

    @property
    def decision_counts(self) -> dict[str, int]:
        counts = Counter(item.decision_action or "none" for item in self.items)
        return dict(sorted(counts.items()))

    @property
    def next_actions(self) -> tuple[SourceCandidateOperatorReportItem, ...]:
        selected = [item for item in self.items if item.recommended_next_action]
        return tuple(selected[: self.policy.max_next_actions])

    def to_json_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": _REPORT_SCHEMA,
            "store_path": str(self.review_audit.review.store_path),
            "snapshot_count": self.review_audit.review.snapshot_count,
            "matched_count": self.review_audit.review.matched_count,
            "returned_count": self.returned_count,
            "audit_indexed_count": self.review_audit.audit_count,
            "audit_present_count": self.audit_present_count,
            "actionable_count": self.actionable_count,
            "terminal_count": self.terminal_count,
            "status_counts": self.status_counts,
            "decision_counts": self.decision_counts,
            "next_actions": [item.to_json_dict() for item in self.next_actions],
            "policy": self.policy.to_json_dict(),
        }
        if self.policy.include_items:
            payload["items"] = [item.to_json_dict() for item in self.items]
        return payload

    def to_text(self) -> str:
        lines = [
            "SourceCandidate operator report",
            f"store: {self.review_audit.review.store_path}",
            f"returned: {self.returned_count}/{self.review_audit.review.matched_count} matched ({self.review_audit.review.snapshot_count} total)",
            f"actionable: {self.actionable_count}",
            f"terminal: {self.terminal_count}",
            f"audits: {self.audit_present_count}/{self.review_audit.audit_count} indexed",
            f"statuses: {_format_counts(self.status_counts)}",
            f"decisions: {_format_counts(self.decision_counts)}",
        ]
        next_actions = self.next_actions
        if not next_actions:
            lines.append("next actions: none")
            return "\n".join(lines)
        lines.append("next actions:")
        for item in next_actions:
            lines.append(
                f"- {item.candidate_id} [{item.status}] {item.recommended_next_action}: {item.title}"
            )
            if item.decision_reason:
                lines.append(f"  reason: {item.decision_reason}")
            if item.target_context_id:
                lines.append(f"  target_context_id: {item.target_context_id}")
        return "\n".join(lines)


def build_source_candidate_operator_report(
    review_audit: SourceCandidateReviewAuditResult,
    policy: SourceCandidateOperatorReportPolicy | None = None,
) -> SourceCandidateOperatorReportResult:
    """Construit un rapport opérateur déterministe depuis une review auditée."""
    effective_policy = policy or SourceCandidateOperatorReportPolicy()
    items = tuple(
        SourceCandidateOperatorReportItem.from_review_audit_item(item)
        for item in review_audit.items
    )
    return SourceCandidateOperatorReportResult(
        review_audit=review_audit,
        policy=effective_policy,
        items=items,
    )


def _recommended_next_action(item: SourceCandidateReviewAuditItem) -> str:
    candidate = item.item.candidate
    if not candidate.actionable:
        if item.audit_present:
            return ""
        return "verify_audit"
    if item.decision is None:
        return "inspect"
    if item.decision.action == "relaunch":
        return "relaunch"
    if item.decision.action == "inspect":
        return "decide"
    return "review"


def _format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())
