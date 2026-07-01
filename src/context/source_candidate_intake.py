from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .source_candidate import (
    SourceCandidate,
    SourceCandidateCreationResult,
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidatePolicy,
    apply_source_candidate_decision,
    build_source_candidate,
)
from .source_candidate_store import (
    SourceCandidateReportPolicy,
    SourceCandidateStorePolicy,
    SourceCandidateStoreWriteResult,
    upsert_source_candidate,
)

_INTAKE_SCHEMA = "missipy.source_candidate.intake_cli.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeCommand:
    """Commande typée d'intake SourceCandidate.

    Cette commande est le payload attendu par le chemin Scheduler vivant introduit
    en Phase 6.1-r1. Elle reste utilisable directement dans des tests unitaires,
    mais le chemin d'intégration passe par ``SourceCandidateIntakeHandler``.
    """

    candidate_input: SourceCandidateInput
    candidate_policy: SourceCandidatePolicy
    store_policy: SourceCandidateStorePolicy
    report_policy: SourceCandidateReportPolicy
    decision: SourceCandidateDecision | None = None


@dataclass(frozen=True, slots=True)
class SourceCandidateIntakeResult:
    """Résultat stable de l'intake SourceCandidate local."""

    creation: SourceCandidateCreationResult
    candidate: SourceCandidate
    write_result: SourceCandidateStoreWriteResult
    decision: SourceCandidateDecision | None
    report_path: Path | None

    @property
    def candidate_id(self) -> str:
        return self.candidate.candidate_id

    @property
    def status(self) -> str:
        return self.candidate.status

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "schema": _INTAKE_SCHEMA,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "terminal": self.candidate.terminal,
            "actionable": self.candidate.actionable,
            "decision": self.decision.to_json_dict() if self.decision is not None else None,
            "store_path": str(self.write_result.path),
            "report_path": str(self.report_path) if self.report_path is not None else None,
            "inserted": self.write_result.inserted,
            "replaced": self.write_result.replaced,
            "candidate_count": self.write_result.snapshot.candidate_count,
            "candidate": self.candidate.to_json_dict(),
            "creation": self.creation.to_json_dict(),
            "write_result": self.write_result.to_json_dict(),
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate intake",
            f"schema: {_INTAKE_SCHEMA}",
            f"candidate_id: {self.candidate_id}",
            f"title: {self.candidate.title}",
            f"status: {self.status}",
            f"terminal: {str(self.candidate.terminal).lower()}",
            f"actionable: {str(self.candidate.actionable).lower()}",
            f"store_path: {self.write_result.path}",
            f"inserted: {str(self.write_result.inserted).lower()}",
            f"replaced: {str(self.write_result.replaced).lower()}",
            f"candidate_count: {self.write_result.snapshot.candidate_count}",
        ]
        if self.decision is not None:
            lines.append(f"decision: {self.decision.action}")
        if self.report_path is not None:
            lines.append(f"report_path: {self.report_path}")
        return "\n".join(lines)


def run_source_candidate_intake(command: SourceCandidateIntakeCommand) -> SourceCandidateIntakeResult:
    """Exécute l'intake local avec un store JSON réel déclaré.

    Cette fonction reste le use-case pur-ish de la feuille : elle applique les
    contrats SourceCandidate, puis franchit la bordure IO SourceCandidateStore.
    Le chemin système passe par le handler Scheduler, qui appelle cette fonction.
    """

    creation = build_source_candidate(command.candidate_input, command.candidate_policy)
    candidate = creation.candidate
    if command.decision is not None:
        candidate = apply_source_candidate_decision(candidate, command.decision)

    report_policy = command.report_policy if command.report_policy.path is not None else None
    write_result = upsert_source_candidate(command.store_policy, candidate, report=report_policy)
    return SourceCandidateIntakeResult(
        creation=creation,
        candidate=candidate,
        write_result=write_result,
        decision=command.decision,
        report_path=command.report_policy.path,
    )
