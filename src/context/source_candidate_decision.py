from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .source_candidate import (
    SourceCandidate,
    SourceCandidateDecision,
    apply_source_candidate_decision,
)
from .source_candidate_store import (
    SourceCandidateReportPolicy,
    SourceCandidateStorePolicy,
    SourceCandidateStoreWriteResult,
    load_source_candidate_store,
    upsert_source_candidate,
)

_DECISION_SCHEMA = "missipy.source_candidate.decision.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateDecisionCommand:
    """Commande typée d'application d'une décision opérateur.

    Le chemin d'intégration attendu est Scheduler -> Dispatcher -> Handler ->
    store JSON réel. Cette commande ne contacte pas GtHub et ne déclenche pas
    de promotion automatique hors du store local.
    """

    store_policy: SourceCandidateStorePolicy
    candidate_id: str
    decision: SourceCandidateDecision
    report_policy: SourceCandidateReportPolicy | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must not be empty")


@dataclass(frozen=True, slots=True)
class SourceCandidateDecisionResult:
    """Résultat observable d'une décision SourceCandidate locale."""

    store_path: Path | str
    candidate_before: SourceCandidate
    candidate_after: SourceCandidate
    write_result: SourceCandidateStoreWriteResult

    def __post_init__(self) -> None:
        object.__setattr__(self, "store_path", Path(self.store_path))

    @property
    def candidate_id(self) -> str:
        return self.candidate_after.candidate_id

    @property
    def action(self) -> str:
        decision = self.candidate_after.decision
        return decision.action if decision is not None else ""

    @property
    def before_status(self) -> str:
        return self.candidate_before.status

    @property
    def after_status(self) -> str:
        return self.candidate_after.status

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _DECISION_SCHEMA,
            "store_path": str(self.store_path),
            "candidate_id": self.candidate_id,
            "action": self.action,
            "before_status": self.before_status,
            "after_status": self.after_status,
            "candidate_before": self.candidate_before.to_json_dict(),
            "candidate_after": self.candidate_after.to_json_dict(),
            "write_result": self.write_result.to_json_dict(),
        }

    def to_text(self) -> str:
        decision = self.candidate_after.decision
        reason = decision.reason if decision is not None and decision.reason else ""
        target = decision.target_context_id if decision is not None else None
        lines = [
            "SourceCandidate decision",
            f"store: {self.store_path}",
            f"candidate: {self.candidate_id}",
            f"action: {self.action}",
            f"status: {self.before_status} -> {self.after_status}",
        ]
        if target:
            lines.append(f"target_context_id: {target}")
        if reason:
            lines.append(f"reason: {reason}")
        return "\n".join(lines)


def run_source_candidate_decision(
    command: SourceCandidateDecisionCommand,
) -> SourceCandidateDecisionResult:
    """Applique une décision opérateur à une candidate existante du store local."""

    snapshot = load_source_candidate_store(command.store_policy)
    candidate = snapshot.find(command.candidate_id)
    if candidate is None:
        raise ValueError(f"unknown SourceCandidate: {command.candidate_id}")

    decided = apply_source_candidate_decision(candidate, command.decision)
    write_result = upsert_source_candidate(
        command.store_policy,
        decided,
        report=command.report_policy,
    )
    return SourceCandidateDecisionResult(
        store_path=command.store_policy.path,
        candidate_before=candidate,
        candidate_after=decided,
        write_result=write_result,
    )
