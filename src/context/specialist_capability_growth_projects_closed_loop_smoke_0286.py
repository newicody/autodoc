"""Closed-loop proof for specialist capability growth in GitHub Projects.

Phase 0286-r8 correlates the immutable r5 publication plan, the bounded r6
operator execution result and the r7 query-only readback evidence.  The module
is pure and performs no GitHub, SQL, Qdrant, Scheduler, EventBus or laboratory
effect.

A coherent provided-snapshot readback closes the deterministic software smoke.
A real deployment is reported closed only when r7 carries valid
``live_query_only`` evidence with ``deployment_ready=True``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (
    SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
)
from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)
from context.specialist_capability_growth_projects_readback_readiness_0286 import (
    SpecialistCapabilityGrowthProjectsReadbackEvidence,
)


SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_SCHEMA = (
    "missipy.specialist.capability_growth.projects_closed_loop_smoke.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_VERSION = "0286.r8"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(ValueError):
    """Raised when the r8 smoke command or result is malformed."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand:
    """Typed inputs for one pure r5/r6/r7 closure check."""

    publication_plan: SpecialistCapabilityGrowthProjectsPublicationPlan
    execution_result: SpecialistCapabilityGrowthProjectsOperatorExecutionResult
    readback_evidence: SpecialistCapabilityGrowthProjectsReadbackEvidence
    require_live_readback: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.publication_plan,
            SpecialistCapabilityGrowthProjectsPublicationPlan,
        ):
            raise TypeError("publication_plan must be the immutable r5 plan")
        if not isinstance(
            self.execution_result,
            SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
        ):
            raise TypeError("execution_result must be the bounded r6 result")
        if not isinstance(
            self.readback_evidence,
            SpecialistCapabilityGrowthProjectsReadbackEvidence,
        ):
            raise TypeError("readback_evidence must be the immutable r7 proof")
        if not isinstance(self.require_live_readback, bool):
            raise TypeError("require_live_readback must be a boolean")


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult:
    """Immutable proof that the 0286 projection loop is correlated."""

    schema: str
    valid: bool
    action: str
    issues: tuple[str, ...]
    source_mode: str
    repository: str
    issue_number: int
    project_id: str
    project_item_id: str
    review_ref: str
    revision_ref: str
    decision_ref: str
    sql_ref: str
    plan_digest: str
    projection_digest_sha256: str
    readback_digest: str
    matched_comment_id: int | None
    plan_execution_correlated: bool
    plan_readback_correlated: bool
    comment_correlated: bool
    projectv2_fields_correlated: bool
    operator_approval_verified: bool
    query_only_readback_verified: bool
    local_contract_closed: bool
    deployment_closed: bool
    phase_0286_closed: bool
    smoke_digest: str
    require_live_readback: bool
    remote_query_performed: bool
    remote_mutation_allowed: bool = field(default=False, init=False)
    github_mutation_performed_by_smoke: bool = field(
        default=False,
        init=False,
    )
    sql_write_performed_by_smoke: bool = field(default=False, init=False)
    qdrant_write_performed_by_smoke: bool = field(default=False, init=False)
    scheduler_dispatch_performed_by_smoke: bool = field(
        default=False,
        init=False,
    )
    eventbus_publication_performed_by_smoke: bool = field(
        default=False,
        init=False,
    )
    laboratory_execution_performed_by_smoke: bool = field(
        default=False,
        init=False,
    )
    github_projects_authoritative: bool = field(default=False, init=False)
    sql_remains_durable_authority: bool = field(default=True, init=False)
    scheduler_remains_only_orchestrator: bool = field(
        default=True,
        init=False,
    )
    qdrant_authoritative: bool = field(default=False, init=False)
    copilot_authoritative: bool = field(default=False, init=False)
    new_http_client_created: bool = field(default=False, init=False)
    new_scheduler_created: bool = field(default=False, init=False)
    new_global_specialist_registry_created: bool = field(
        default=False,
        init=False,
    )

    def __post_init__(self) -> None:
        if self.schema != (
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_SCHEMA
        ):
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "unsupported closed-loop smoke schema"
            )
        if self.action not in {
            "local_contract_closed",
            "deployment_closed",
            "blocked",
        }:
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "unsupported closed-loop smoke action"
            )
        if self.valid != (not self.issues and self.phase_0286_closed):
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "valid flag does not match issues/phase closure"
            )
        if self.deployment_closed and (
            not self.local_contract_closed
            or self.source_mode != "live_query_only"
            or not self.remote_query_performed
        ):
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "deployment closure requires valid live query-only readback"
            )
        if self.require_live_readback and self.valid and not self.deployment_closed:
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "a valid live-required smoke must close the deployment"
            )
        if not _SHA256_RE.fullmatch(self.smoke_digest):
            raise SpecialistCapabilityGrowthProjectsClosedLoopSmokeError(
                "smoke_digest must be a lowercase SHA-256"
            )
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "action": self.action,
            "issues": list(self.issues),
            "source_mode": self.source_mode,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "project_id": self.project_id,
            "project_item_id": self.project_item_id,
            "review_ref": self.review_ref,
            "revision_ref": self.revision_ref,
            "decision_ref": self.decision_ref,
            "sql_ref": self.sql_ref,
            "plan_digest": self.plan_digest,
            "projection_digest_sha256": self.projection_digest_sha256,
            "readback_digest": self.readback_digest,
            "matched_comment_id": self.matched_comment_id,
            "plan_execution_correlated": self.plan_execution_correlated,
            "plan_readback_correlated": self.plan_readback_correlated,
            "comment_correlated": self.comment_correlated,
            "projectv2_fields_correlated": self.projectv2_fields_correlated,
            "operator_approval_verified": self.operator_approval_verified,
            "query_only_readback_verified": self.query_only_readback_verified,
            "local_contract_closed": self.local_contract_closed,
            "deployment_closed": self.deployment_closed,
            "phase_0286_closed": self.phase_0286_closed,
            "smoke_digest": self.smoke_digest,
            "require_live_readback": self.require_live_readback,
            "remote_query_performed": self.remote_query_performed,
            "remote_mutation_allowed": False,
            "github_mutation_performed_by_smoke": False,
            "sql_write_performed_by_smoke": False,
            "qdrant_write_performed_by_smoke": False,
            "scheduler_dispatch_performed_by_smoke": False,
            "eventbus_publication_performed_by_smoke": False,
            "laboratory_execution_performed_by_smoke": False,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "copilot_authoritative": False,
            "new_http_client_created": False,
            "new_scheduler_created": False,
            "new_global_specialist_registry_created": False,
        }


def run_specialist_capability_growth_projects_closed_loop_smoke(
    command: SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand,
) -> SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult:
    """Verify exact r5/r6/r7 correlation without performing effects."""

    plan = command.publication_plan
    execution = command.execution_result
    readback = command.readback_evidence
    issues: list[str] = []

    plan_execution_issues = _validate_plan_execution(plan, execution)
    plan_readback_issues = _validate_plan_readback(plan, readback)
    issues.extend(plan_execution_issues)
    issues.extend(plan_readback_issues)

    plan_execution_correlated = not plan_execution_issues
    plan_readback_correlated = not plan_readback_issues
    comment_correlated = (
        readback.issue_comment_verified
        and readback.comment_body_sha256 == plan.comment_body_sha256
        and (
            execution.comment_id is None
            or readback.matched_comment_id == execution.comment_id
        )
    )
    if not comment_correlated:
        issues.append("Issue comment is not correlated across r5/r6/r7")

    projectv2_fields_correlated = (
        readback.projectv2_fields_verified
        and tuple(sorted(readback.expected_projectv2_field_values))
        == tuple(sorted(plan.projectv2_field_values))
        and tuple(sorted(readback.actual_projectv2_field_values))
        == tuple(sorted(plan.projectv2_field_values))
    )
    if not projectv2_fields_correlated:
        issues.append("ProjectV2 fields are not correlated across r5/r7")

    operator_approval_verified = (
        execution.operator_decision == "approve"
        and execution.mode == "execute"
        and execution.action in {"executed", "replayed"}
        and execution.remote_mutation_allowed
        and execution.confirmed_plan_digest == plan.plan_digest
    )
    if not operator_approval_verified:
        issues.append("r6 operator approval or exact digest is not verified")

    query_only_readback_verified = (
        readback.query_only
        and not readback.remote_mutation_allowed
        and not readback.github_mutation_performed
        and not readback.issue_comment_published
        and not readback.projectv2_mutation_performed
        and readback.readback_ready
        and readback.valid
    )
    if not query_only_readback_verified:
        issues.append("r7 readback is not a valid query-only proof")

    issues = list(dict.fromkeys(issues))
    local_contract_closed = not issues
    deployment_closed = (
        local_contract_closed
        and readback.deployment_ready
        and readback.source_mode == "live_query_only"
        and readback.remote_query_performed
    )
    if command.require_live_readback and not deployment_closed:
        issues.append(
            "live query-only deployment evidence is required but absent"
        )
        local_contract_closed = False

    phase_0286_closed = local_contract_closed
    valid = phase_0286_closed and not issues
    action = (
        "deployment_closed"
        if valid and deployment_closed
        else "local_contract_closed"
        if valid
        else "blocked"
    )
    smoke_digest = _smoke_digest(
        plan=plan,
        execution=execution,
        readback=readback,
        require_live_readback=command.require_live_readback,
        issues=issues,
    )

    return SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult(
        schema=(
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_SCHEMA
        ),
        valid=valid,
        action=action,
        issues=tuple(issues),
        source_mode=readback.source_mode,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        review_ref=plan.review_ref,
        revision_ref=plan.revision_ref,
        decision_ref=plan.decision_ref,
        sql_ref=plan.sql_ref,
        plan_digest=plan.plan_digest,
        projection_digest_sha256=plan.projection_digest_sha256,
        readback_digest=readback.readback_digest,
        matched_comment_id=readback.matched_comment_id,
        plan_execution_correlated=plan_execution_correlated,
        plan_readback_correlated=plan_readback_correlated,
        comment_correlated=comment_correlated,
        projectv2_fields_correlated=projectv2_fields_correlated,
        operator_approval_verified=operator_approval_verified,
        query_only_readback_verified=query_only_readback_verified,
        local_contract_closed=local_contract_closed,
        deployment_closed=deployment_closed,
        phase_0286_closed=phase_0286_closed,
        smoke_digest=smoke_digest,
        require_live_readback=command.require_live_readback,
        remote_query_performed=readback.remote_query_performed,
    )


def _validate_plan_execution(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    execution: SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not plan.valid or plan.action in {"collision", "blocked"}:
        issues.append("r5 publication plan is invalid or blocked")
    if not execution.valid:
        issues.append("r6 execution result is invalid")
    pairs = (
        ("plan_digest", execution.plan_digest, plan.plan_digest),
        (
            "confirmed_plan_digest",
            execution.confirmed_plan_digest,
            plan.plan_digest,
        ),
        ("repository", execution.repository, plan.repository),
        ("issue_number", execution.issue_number, plan.issue_number),
        ("project_id", execution.project_id, plan.project_id),
        ("project_item_id", execution.project_item_id, plan.project_item_id),
    )
    for label, actual, expected in pairs:
        if actual != expected:
            issues.append(f"r6 {label} differs from the r5 plan")
    return tuple(dict.fromkeys(issues))


def _validate_plan_readback(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    readback: SpecialistCapabilityGrowthProjectsReadbackEvidence,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not readback.valid or not readback.readback_ready:
        issues.append("r7 readback evidence is invalid or not ready")
    pairs = (
        ("plan_digest", readback.plan_digest, plan.plan_digest),
        ("repository", readback.repository, plan.repository),
        ("issue_number", readback.issue_number, plan.issue_number),
        ("project_id", readback.project_id, plan.project_id),
        ("project_item_id", readback.project_item_id, plan.project_item_id),
        ("revision_ref", readback.revision_ref, plan.revision_ref),
        ("decision_ref", readback.decision_ref, plan.decision_ref),
        ("sql_ref", readback.sql_ref, plan.sql_ref),
        ("marker", readback.marker, plan.marker),
    )
    for label, actual, expected in pairs:
        if actual != expected:
            issues.append(f"r7 {label} differs from the r5 plan")
    return tuple(dict.fromkeys(issues))


def _smoke_digest(
    *,
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    execution: SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
    readback: SpecialistCapabilityGrowthProjectsReadbackEvidence,
    require_live_readback: bool,
    issues: Sequence[str],
) -> str:
    payload = {
        "schema": (
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_SCHEMA
        ),
        "repository": plan.repository,
        "issue_number": plan.issue_number,
        "project_id": plan.project_id,
        "project_item_id": plan.project_item_id,
        "review_ref": plan.review_ref,
        "revision_ref": plan.revision_ref,
        "decision_ref": plan.decision_ref,
        "sql_ref": plan.sql_ref,
        "plan_digest": plan.plan_digest,
        "execution_action": execution.action,
        "readback_digest": readback.readback_digest,
        "source_mode": readback.source_mode,
        "require_live_readback": require_live_readback,
        "issues": list(issues),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_CLOSED_LOOP_SMOKE_VERSION",
    "SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand",
    "SpecialistCapabilityGrowthProjectsClosedLoopSmokeError",
    "SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult",
    "run_specialist_capability_growth_projects_closed_loop_smoke",
)
