from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

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
_AUDIT_SCHEMA = "missipy.source_candidate.decision_audit.v1"


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
    audit_policy: SourceCandidateDecisionAuditPolicy | None = None

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
    audit_path: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "store_path", Path(self.store_path))
        if self.audit_path is not None:
            object.__setattr__(self, "audit_path", Path(self.audit_path))

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
            "audit_path": str(self.audit_path) if self.audit_path is not None else None,
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
        if self.audit_path is not None:
            lines.append(f"audit: {self.audit_path}")
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class SourceCandidateDecisionAuditPolicy:
    """Politique de rapport audit local pour une décision opérateur."""

    path: Path | str
    include_candidates: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if not str(self.path):
            raise ValueError("audit path must not be empty")


@dataclass(frozen=True, slots=True)
class SourceCandidateDecisionAuditRecord:
    """Enregistrement stable d'audit après décision locale."""

    result: SourceCandidateDecisionResult
    include_candidates: bool = True

    def to_json_dict(self) -> dict[str, object]:
        decision = self.result.candidate_after.decision
        payload: dict[str, object] = {
            "schema": _AUDIT_SCHEMA,
            "operation": "source_candidate_decision",
            "store_path": str(self.result.store_path),
            "candidate_id": self.result.candidate_id,
            "action": self.result.action,
            "before_status": self.result.before_status,
            "after_status": self.result.after_status,
            "reason": decision.reason if decision is not None else "",
            "target_context_id": decision.target_context_id if decision is not None else None,
            "write_result": self.result.write_result.to_json_dict(),
        }
        if self.include_candidates:
            payload["candidate_before"] = self.result.candidate_before.to_json_dict()
            payload["candidate_after"] = self.result.candidate_after.to_json_dict()
        return payload


def write_source_candidate_decision_audit(
    policy: SourceCandidateDecisionAuditPolicy,
    result: SourceCandidateDecisionResult,
) -> Path:
    """Écrit atomiquement un rapport audit JSON local."""

    path = Path(policy.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = SourceCandidateDecisionAuditRecord(
        result=result,
        include_candidates=policy.include_candidates,
    )
    payload = record.to_json_dict()
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        delete=False,
    ) as handle:
        tmp_path = Path(handle.name)
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    tmp_path.replace(path)
    return path


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
    result = SourceCandidateDecisionResult(
        store_path=command.store_policy.path,
        candidate_before=candidate,
        candidate_after=decided,
        write_result=write_result,
    )
    if command.audit_policy is None:
        return result

    audit_path = write_source_candidate_decision_audit(command.audit_policy, result)
    return SourceCandidateDecisionResult(
        store_path=result.store_path,
        candidate_before=result.candidate_before,
        candidate_after=result.candidate_after,
        write_result=result.write_result,
        audit_path=audit_path,
    )
