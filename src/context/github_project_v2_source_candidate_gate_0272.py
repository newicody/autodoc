"""Operator gate for ProjectV2 SourceCandidate handoffs.

This phase reuses the existing SourceCandidate decision contract.  It reads one
immutable r6 handoff batch, applies one explicit local operator decision and
produces one immutable gate record.  It performs no GitHub call, no SQL/Qdrant
write and no Scheduler or SHM modification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

from context.github_project_v2_change_handoff_0272 import HANDOFF_BATCH_SCHEMA
from context.source_candidate import (
    SourceCandidateDecision,
    allowed_source_candidate_decisions,
    apply_source_candidate_decision,
)
from context.source_candidate_store import source_candidate_store_snapshot_from_json_dict

GATE_RECORD_SCHEMA = "missipy.github.project_v2_source_candidate_gate.v1"
GATE_REPORT_SCHEMA = "missipy.github.project_v2_source_candidate_gate_report.v1"
_APPROVING_ACTIONS = frozenset({"promote", "merge"})


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SourceCandidateGateCommand:
    candidate_id: str
    action: str
    reason: str = ""
    target_context_id: str | None = None
    execute: bool = False
    policy_decision_id: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.action not in allowed_source_candidate_decisions():
            raise ValueError(
                "action must be inspect, relaunch, reject, archive, promote or merge"
            )
        if self.action == "merge" and not (self.target_context_id or "").strip():
            raise ValueError("target_context_id is required for merge")


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SourceCandidateGatePlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    handoff_batch_path: str
    candidate_id: str
    action: str
    boundaries: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class GitHubProjectV2SourceCandidateGateResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    handoff_batch_ref: str
    handoff_ref: str
    candidate_id: str
    action: str
    before_status: str
    after_status: str
    gate_ref: str
    gate_path: str
    durable_ingestion_allowed: bool
    ingestion_mode: str
    external_call_performed: bool = False
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": GATE_REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "handoff_batch_ref": self.handoff_batch_ref,
            "handoff_ref": self.handoff_ref,
            "candidate_id": self.candidate_id,
            "action": self.action,
            "before_status": self.before_status,
            "after_status": self.after_status,
            "gate_ref": self.gate_ref,
            "gate_path": self.gate_path,
            "durable_ingestion_allowed": self.durable_ingestion_allowed,
            "ingestion_mode": self.ingestion_mode,
            "external_call_performed": self.external_call_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_source_candidate_gate_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"candidate_id={self.candidate_id or '-'}",
                f"action={self.action or '-'}",
                f"status={self.before_status or '-'}->{self.after_status or '-'}",
                f"gate_ref={self.gate_ref or '-'}",
                f"durable_ingestion_allowed={self.durable_ingestion_allowed}",
                f"ingestion_mode={self.ingestion_mode}",
                "external_call_performed=False",
                "sql_write_performed=False",
                "qdrant_write_performed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_gate_plan(
    command: GitHubProjectV2SourceCandidateGateCommand,
    *,
    handoff_batch_path: str,
) -> GitHubProjectV2SourceCandidateGatePlan:
    issues: list[str] = []
    if not handoff_batch_path.strip():
        issues.append("handoff batch path is required")
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    return GitHubProjectV2SourceCandidateGatePlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        handoff_batch_path=handoff_batch_path,
        candidate_id=command.candidate_id,
        action=command.action,
        boundaries=_boundaries(False),
    )


def validate_handoff_batch(payload: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if str(payload.get("schema", "")) != HANDOFF_BATCH_SCHEMA:
        issues.append("handoff batch schema mismatch")
    if not str(payload.get("handoff_batch_ref", "")).startswith(
        "github-project-v2-handoff-batch:"
    ):
        issues.append("handoff_batch_ref is invalid")
    handoffs = payload.get("handoffs")
    if not isinstance(handoffs, list):
        issues.append("handoffs must be a list")
    boundaries = _mapping(payload.get("boundaries"))
    for key in (
        "external_call_performed",
        "graphql_mutation_allowed",
        "remote_mutation_allowed",
        "sql_write_allowed",
        "qdrant_write_allowed",
    ):
        if boundaries.get(key) is not False:
            issues.append(f"handoff batch boundary must forbid {key}")
    return tuple(issues)


def build_gate_record(
    *,
    handoff_batch: Mapping[str, Any],
    command: GitHubProjectV2SourceCandidateGateCommand,
) -> dict[str, Any]:
    issues = validate_handoff_batch(handoff_batch)
    if issues:
        raise ValueError("; ".join(issues))
    handoff = _find_handoff(handoff_batch, command.candidate_id)
    if handoff is None:
        raise ValueError(f"candidate not found in handoff batch: {command.candidate_id}")
    if handoff.get("requires_operator_gate") is not True:
        raise ValueError("handoff does not require an operator gate")
    if handoff.get("durable_ingestion_allowed") is not False:
        raise ValueError("ungated handoff must forbid durable ingestion")

    change_kind = str(handoff.get("change_kind", ""))
    if change_kind == "removed" and command.action in _APPROVING_ACTIONS:
        raise ValueError("removed ProjectV2 items are advisory and cannot be promoted or merged")

    candidate_payload = _mapping(handoff.get("candidate"))
    snapshot = source_candidate_store_snapshot_from_json_dict(
        {
            "schema": "missipy.source_candidate.store.v1",
            "repository": _candidate_repository(candidate_payload),
            "metadata": {
                "source": "github_project_v2_change_handoff_0272",
                "handoff_batch_ref": str(handoff_batch.get("handoff_batch_ref", "")),
            },
            "candidates": [dict(candidate_payload)],
        }
    )
    if len(snapshot.candidates) != 1:
        raise ValueError("candidate reconstruction must produce exactly one candidate")
    candidate_before = snapshot.candidates[0]
    decision = SourceCandidateDecision(
        action=command.action,
        reason=command.reason,
        target_context_id=command.target_context_id,
    )
    candidate_after = apply_source_candidate_decision(candidate_before, decision)
    durable_allowed = command.action in _APPROVING_ACTIONS
    ingestion_mode = command.action if durable_allowed else "none"
    record: dict[str, Any] = {
        "schema": GATE_RECORD_SCHEMA,
        "kind": "github_project_v2_source_candidate_gate",
        "policy_decision_id": command.policy_decision_id,
        "handoff_batch_ref": str(handoff_batch.get("handoff_batch_ref", "")),
        "handoff_ref": str(handoff.get("handoff_ref", "")),
        "change_kind": change_kind,
        "candidate_id": candidate_after.candidate_id,
        "decision": decision.to_json_dict(),
        "candidate_before": candidate_before.to_json_dict(),
        "candidate_after": candidate_after.to_json_dict(),
        "approval": {
            "durable_ingestion_allowed": durable_allowed,
            "ingestion_mode": ingestion_mode,
            "target_context_id": command.target_context_id,
            "durable_ingestion_performed": False,
        },
        "boundaries": _boundaries(durable_allowed),
    }
    digest = hashlib.sha256(_canonical_json(record).encode("utf-8")).hexdigest()[:16]
    record["gate_ref"] = f"github-project-v2-source-candidate-gate:{digest}"
    return record


def close_gate_result(
    plan: GitHubProjectV2SourceCandidateGatePlan,
    *,
    gate_record: Mapping[str, Any] | None,
    gate_path: str,
    errors: Sequence[str] = (),
) -> GitHubProjectV2SourceCandidateGateResult:
    issues = list(plan.issues)
    issues.extend(str(error) for error in errors if str(error))
    payload = dict(gate_record or {})
    if plan.execute:
        if not payload:
            issues.append("execute mode must produce a gate record")
        elif str(payload.get("schema", "")) != GATE_RECORD_SCHEMA:
            issues.append("gate record schema mismatch")
    elif payload:
        issues.append("plan-only mode must not contain a gate record")
    decision = _mapping(payload.get("decision"))
    before = _mapping(payload.get("candidate_before"))
    after = _mapping(payload.get("candidate_after"))
    approval = _mapping(payload.get("approval"))
    durable_allowed = bool(approval.get("durable_ingestion_allowed", False))
    return GitHubProjectV2SourceCandidateGateResult(
        valid=not issues,
        issues=tuple(dict.fromkeys(issues)),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        handoff_batch_ref=str(payload.get("handoff_batch_ref", "")),
        handoff_ref=str(payload.get("handoff_ref", "")),
        candidate_id=str(payload.get("candidate_id", plan.candidate_id)),
        action=str(decision.get("action", plan.action)),
        before_status=str(before.get("status", "")),
        after_status=str(after.get("status", "")),
        gate_ref=str(payload.get("gate_ref", "")),
        gate_path=gate_path,
        durable_ingestion_allowed=durable_allowed,
        ingestion_mode=str(approval.get("ingestion_mode", "none")),
        boundaries=_mapping(payload.get("boundaries")) or _boundaries(False),
    )


def _find_handoff(
    handoff_batch: Mapping[str, Any],
    candidate_id: str,
) -> Mapping[str, Any] | None:
    handoffs = handoff_batch.get("handoffs", [])
    if not isinstance(handoffs, list):
        return None
    for handoff in handoffs:
        if not isinstance(handoff, Mapping):
            continue
        candidate = _mapping(handoff.get("candidate"))
        if str(candidate.get("candidate_id", "")) == candidate_id:
            return handoff
    return None


def _candidate_repository(candidate: Mapping[str, Any]) -> str | None:
    repository = _mapping(candidate.get("origin")).get("repository")
    if repository is None:
        return None
    return str(repository)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _boundaries(durable_ingestion_allowed: bool) -> dict[str, bool]:
    return {
        "existing_source_candidate_decision_reused": True,
        "operator_gate_applied": True,
        "durable_ingestion_allowed": durable_ingestion_allowed,
        "durable_ingestion_performed": False,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "sql_write_allowed": False,
        "sql_write_performed": False,
        "qdrant_write_allowed": False,
        "qdrant_write_performed": False,
        "scheduler_modified": False,
        "shm_modified": False,
        "local_authority_preserved": True,
    }
