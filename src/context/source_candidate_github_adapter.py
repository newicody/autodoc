from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .source_candidate_remote_mutation_gate import (
    SourceCandidateRemoteMutationGatePolicy,
    SourceCandidateRemoteMutationGateResult,
    run_source_candidate_remote_mutation_gate,
)


_ADAPTER_PLAN_SCHEMA = "missipy.source_candidate.github_adapter_plan.v1"
_ADAPTER_DRY_RUN_SCHEMA = "missipy.source_candidate.github_adapter_dry_run.v1"
_ADAPTER_APPLY_SCHEMA = "missipy.source_candidate.github_adapter_apply.v1"


@dataclass(frozen=True)
class SourceCandidateGithubAdapterOperationPlan:
    action: str
    candidate_id: str
    title: str
    labels: tuple[str, ...]
    safety_flags: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "candidate_id": self.candidate_id,
            "title": self.title,
            "labels": list(self.labels),
            "safety_flags": list(self.safety_flags),
        }


@dataclass(frozen=True)
class SourceCandidateGithubAdapterPlan:
    repository: str
    project_key: str | None
    dry_run: bool
    remote_mutation: bool
    operation_count: int
    operations: tuple[SourceCandidateGithubAdapterOperationPlan, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _ADAPTER_PLAN_SCHEMA,
            "repository": self.repository,
            "project_key": self.project_key,
            "dry_run": self.dry_run,
            "remote_mutation": self.remote_mutation,
            "operation_count": self.operation_count,
            "operations": [operation.to_json_dict() for operation in self.operations],
        }


@dataclass(frozen=True)
class SourceCandidateGithubAdapterDryRun:
    plan: SourceCandidateGithubAdapterPlan
    gate: SourceCandidateRemoteMutationGateResult

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _ADAPTER_DRY_RUN_SCHEMA,
            "plan": self.plan.to_json_dict(),
            "gate": self.gate.to_json_dict(),
        }


@dataclass(frozen=True)
class SourceCandidateGithubAdapterApplyResult:
    applied: bool
    fake_only: bool
    operation_count: int
    blocked_reasons: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _ADAPTER_APPLY_SCHEMA,
            "applied": self.applied,
            "fake_only": self.fake_only,
            "operation_count": self.operation_count,
            "blocked_reasons": list(self.blocked_reasons),
        }


class SourceCandidateGithubProjectionAdapter(Protocol):
    """Interface for a future GitHub projection adapter.

    Implementations must keep planning, validation, dry-run and apply separated.
    The Phase 7.4 implementation is fake-only.
    """

    def plan(self, payload: Mapping[str, Any]) -> SourceCandidateGithubAdapterPlan:
        ...

    def dry_run(
        self,
        payload: Mapping[str, Any],
        policy: SourceCandidateRemoteMutationGatePolicy,
    ) -> SourceCandidateGithubAdapterDryRun:
        ...

    def apply(
        self,
        payload: Mapping[str, Any],
        policy: SourceCandidateRemoteMutationGatePolicy,
    ) -> SourceCandidateGithubAdapterApplyResult:
        ...


@dataclass
class FakeSourceCandidateGithubProjectionAdapter:
    """Fake GitHub adapter used for local tests and operator review.

    The fake adapter records local apply simulations only when the remote
    mutation gate passes. It never contacts GitHub.
    """

    applied_payloads: list[dict[str, object]] = field(default_factory=list)

    def plan(self, payload: Mapping[str, Any]) -> SourceCandidateGithubAdapterPlan:
        operations = tuple(_operation_plan(operation) for operation in _operations(payload))
        return SourceCandidateGithubAdapterPlan(
            repository=_string(payload.get("repository")),
            project_key=_optional_string(payload.get("project_key")),
            dry_run=bool(payload.get("dry_run")),
            remote_mutation=bool(payload.get("remote_mutation")),
            operation_count=len(operations),
            operations=operations,
        )

    def dry_run(
        self,
        payload: Mapping[str, Any],
        policy: SourceCandidateRemoteMutationGatePolicy,
    ) -> SourceCandidateGithubAdapterDryRun:
        return SourceCandidateGithubAdapterDryRun(
            plan=self.plan(payload),
            gate=run_source_candidate_remote_mutation_gate(payload, policy),
        )

    def apply(
        self,
        payload: Mapping[str, Any],
        policy: SourceCandidateRemoteMutationGatePolicy,
    ) -> SourceCandidateGithubAdapterApplyResult:
        dry_run = self.dry_run(payload, policy)
        if not dry_run.gate.mutation_allowed:
            return SourceCandidateGithubAdapterApplyResult(
                applied=False,
                fake_only=True,
                operation_count=0,
                blocked_reasons=tuple(issue.code for issue in dry_run.gate.issues),
            )

        plan_payload = dry_run.plan.to_json_dict()
        self.applied_payloads.append(plan_payload)
        return SourceCandidateGithubAdapterApplyResult(
            applied=True,
            fake_only=True,
            operation_count=dry_run.plan.operation_count,
            blocked_reasons=(),
        )


def _operation_plan(raw: Mapping[str, Any]) -> SourceCandidateGithubAdapterOperationPlan:
    return SourceCandidateGithubAdapterOperationPlan(
        action=_string(raw.get("action")),
        candidate_id=_string(raw.get("candidate_id")),
        title=_string(raw.get("title")),
        labels=tuple(_string(item) for item in _sequence(raw.get("labels"))),
        safety_flags=tuple(_string(item) for item in _sequence(raw.get("safety_flags"))),
    )


def _operations(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw = payload.get("operations")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise ValueError("payload operations must be a list")
    operations: list[Mapping[str, Any]] = []
    for operation in raw:
        if not isinstance(operation, Mapping):
            raise ValueError("payload operation must be an object")
        operations.append(operation)
    return tuple(operations)


def _sequence(raw: object) -> tuple[object, ...]:
    if raw is None:
        return ()
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        return tuple(raw)
    raise ValueError("expected list")


def _string(raw: object) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw
    raise ValueError("expected non-empty string")


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw
    return None
