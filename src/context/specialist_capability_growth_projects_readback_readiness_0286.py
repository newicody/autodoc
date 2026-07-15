"""Query-only readback evidence for capability-growth GitHub projection.

Phase 0286-r7 correlates the immutable r5 publication plan, the bounded r6
operator execution result, the remote Issue comment and the ProjectV2 field
values.  This module is pure: it performs no network access and no mutation.
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

SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA = (
    "missipy.specialist.capability_growth.projects_readback.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_VERSION = "0286.r7"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SpecialistCapabilityGrowthProjectsReadbackError(ValueError):
    """Raised when a readback command or snapshot is malformed."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthIssueCommentReadback:
    """One query-only Issue comment snapshot."""

    comment_id: int
    body: str
    html_url: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.comment_id, int) or self.comment_id <= 0:
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "comment_id must be a positive integer"
            )
        if not isinstance(self.body, str):
            raise TypeError("comment body must be a string")
        if not isinstance(self.html_url, str):
            raise TypeError("comment html_url must be a string")


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsReadbackCommand:
    """Typed inputs for one pure readback verification."""

    publication_plan: SpecialistCapabilityGrowthProjectsPublicationPlan
    execution_result: SpecialistCapabilityGrowthProjectsOperatorExecutionResult
    issue_comments: tuple[SpecialistCapabilityGrowthIssueCommentReadback, ...]
    projectv2_field_values: tuple[tuple[str, str], ...]
    source_mode: str = "provided_snapshots"

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
        if self.source_mode not in {"provided_snapshots", "live_query_only"}:
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "source_mode must be provided_snapshots or live_query_only"
            )
        object.__setattr__(self, "issue_comments", tuple(self.issue_comments))
        object.__setattr__(
            self,
            "projectv2_field_values",
            _normalize_field_values(self.projectv2_field_values),
        )


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsReadbackEvidence:
    """Immutable evidence that the intended projection can be read back."""

    schema: str
    valid: bool
    action: str
    issues: tuple[str, ...]
    source_mode: str
    repository: str
    issue_number: int
    project_id: str
    project_item_id: str
    plan_digest: str
    marker: str
    sql_ref: str
    revision_ref: str
    decision_ref: str
    matched_comment_id: int | None
    matched_comment_url: str
    comment_body_sha256: str
    expected_projectv2_field_values: tuple[tuple[str, str], ...]
    actual_projectv2_field_values: tuple[tuple[str, str], ...]
    publication_execution_verified: bool
    issue_comment_verified: bool
    projectv2_fields_verified: bool
    readback_ready: bool
    deployment_ready: bool
    readback_digest: str
    query_only: bool = field(default=True, init=False)
    remote_query_performed: bool = field(default=False)
    remote_mutation_allowed: bool = field(default=False, init=False)
    github_mutation_performed: bool = field(default=False, init=False)
    issue_comment_published: bool = field(default=False, init=False)
    projectv2_mutation_performed: bool = field(default=False, init=False)
    github_projects_authoritative: bool = field(default=False, init=False)
    sql_remains_durable_authority: bool = field(default=True, init=False)
    scheduler_remains_only_orchestrator: bool = field(default=True, init=False)
    qdrant_authoritative: bool = field(default=False, init=False)
    copilot_authoritative: bool = field(default=False, init=False)
    new_http_client_created: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA:
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "unsupported readback evidence schema"
            )
        if self.action not in {
            "snapshot_ready",
            "deployment_ready",
            "drift_detected",
        }:
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "unsupported readback evidence action"
            )
        if self.valid != (not self.issues and self.readback_ready):
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "valid flag does not match issues/readback readiness"
            )
        if self.deployment_ready and (
            not self.valid
            or self.source_mode != "live_query_only"
            or not self.remote_query_performed
        ):
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "deployment_ready requires a valid live query-only readback"
            )
        if not _SHA256_RE.fullmatch(self.readback_digest):
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "readback_digest must be a lowercase SHA-256"
            )
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(
            self,
            "expected_projectv2_field_values",
            tuple(self.expected_projectv2_field_values),
        )
        object.__setattr__(
            self,
            "actual_projectv2_field_values",
            tuple(self.actual_projectv2_field_values),
        )

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
            "plan_digest": self.plan_digest,
            "marker": self.marker,
            "sql_ref": self.sql_ref,
            "revision_ref": self.revision_ref,
            "decision_ref": self.decision_ref,
            "matched_comment_id": self.matched_comment_id,
            "matched_comment_url": self.matched_comment_url,
            "comment_body_sha256": self.comment_body_sha256,
            "expected_projectv2_field_values": dict(
                self.expected_projectv2_field_values
            ),
            "actual_projectv2_field_values": dict(
                self.actual_projectv2_field_values
            ),
            "publication_execution_verified": (
                self.publication_execution_verified
            ),
            "issue_comment_verified": self.issue_comment_verified,
            "projectv2_fields_verified": self.projectv2_fields_verified,
            "readback_ready": self.readback_ready,
            "deployment_ready": self.deployment_ready,
            "readback_digest": self.readback_digest,
            "query_only": True,
            "remote_query_performed": self.remote_query_performed,
            "remote_mutation_allowed": False,
            "github_mutation_performed": False,
            "issue_comment_published": False,
            "projectv2_mutation_performed": False,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "copilot_authoritative": False,
            "new_http_client_created": False,
        }


def verify_specialist_capability_growth_projects_readback(
    command: SpecialistCapabilityGrowthProjectsReadbackCommand,
) -> SpecialistCapabilityGrowthProjectsReadbackEvidence:
    """Correlate plan, execution and query-only remote snapshots."""

    plan = command.publication_plan
    execution = command.execution_result
    issues: list[str] = []

    if not plan.valid or plan.action in {"collision", "blocked"}:
        issues.append("publication plan is not valid for readback")

    execution_issues = _validate_execution(plan, execution)
    issues.extend(execution_issues)
    publication_execution_verified = not execution_issues

    matching_comments = tuple(
        comment for comment in command.issue_comments if plan.marker in comment.body
    )
    matched_comment = (
        matching_comments[0] if len(matching_comments) == 1 else None
    )
    if not matching_comments:
        issues.append("readback did not find the idempotency marker")
    elif len(matching_comments) > 1:
        issues.append("readback found multiple comments with the same marker")

    issue_comment_verified = False
    actual_comment_digest = sha256(b"").hexdigest()
    if matched_comment is not None:
        actual_comment_digest = sha256(
            matched_comment.body.encode("utf-8")
        ).hexdigest()
        if matched_comment.body != plan.comment_body:
            issues.append("readback Issue comment body drifted from the plan")
        elif actual_comment_digest != plan.comment_body_sha256:
            issues.append("readback Issue comment digest drifted from the plan")
        elif (
            execution.comment_id is not None
            and execution.comment_id != matched_comment.comment_id
        ):
            issues.append(
                "readback Issue comment id differs from the execution result"
            )
        else:
            issue_comment_verified = True

    expected_values = tuple(plan.projectv2_field_values)
    actual_values = command.projectv2_field_values
    actual_by_name = dict(actual_values)
    field_issues: list[str] = []
    for field_name, desired_value in expected_values:
        if field_name not in actual_by_name:
            field_issues.append(f"missing ProjectV2 field: {field_name}")
        elif actual_by_name[field_name] != desired_value:
            field_issues.append(
                f"ProjectV2 field drift: {field_name}"
            )
    issues.extend(field_issues)
    projectv2_fields_verified = not field_issues

    issues = list(dict.fromkeys(issues))
    readback_ready = not issues
    deployment_ready = (
        readback_ready and command.source_mode == "live_query_only"
    )
    action = (
        "deployment_ready"
        if deployment_ready
        else "snapshot_ready"
        if readback_ready
        else "drift_detected"
    )
    digest = _readback_digest(
        plan=plan,
        execution=execution,
        source_mode=command.source_mode,
        matched_comment=matched_comment,
        actual_comment_digest=actual_comment_digest,
        actual_field_values=actual_values,
        issues=issues,
    )

    return SpecialistCapabilityGrowthProjectsReadbackEvidence(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA,
        valid=readback_ready,
        action=action,
        issues=tuple(issues),
        source_mode=command.source_mode,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        plan_digest=plan.plan_digest,
        marker=plan.marker,
        sql_ref=plan.sql_ref,
        revision_ref=plan.revision_ref,
        decision_ref=plan.decision_ref,
        matched_comment_id=(
            matched_comment.comment_id if matched_comment is not None else None
        ),
        matched_comment_url=(
            matched_comment.html_url if matched_comment is not None else ""
        ),
        comment_body_sha256=actual_comment_digest,
        expected_projectv2_field_values=expected_values,
        actual_projectv2_field_values=actual_values,
        publication_execution_verified=publication_execution_verified,
        issue_comment_verified=issue_comment_verified,
        projectv2_fields_verified=projectv2_fields_verified,
        readback_ready=readback_ready,
        deployment_ready=deployment_ready,
        readback_digest=digest,
        remote_query_performed=command.source_mode == "live_query_only",
    )


def _validate_execution(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    execution: SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not execution.valid:
        issues.append("operator execution result is not valid")
    if execution.mode != "execute":
        issues.append("readback requires an executed or replayed r6 result")
    if execution.action not in {"executed", "replayed"}:
        issues.append("operator execution action is not executed/replayed")
    if execution.operator_decision != "approve":
        issues.append("operator execution did not preserve approve")
    if execution.plan_digest != plan.plan_digest:
        issues.append("execution plan_digest differs from the r5 plan")
    if execution.confirmed_plan_digest != plan.plan_digest:
        issues.append("execution did not confirm the exact plan_digest")
    if not execution.remote_mutation_allowed:
        issues.append("r6 execution boundary was not explicitly authorized")
    identity_pairs = (
        ("repository", execution.repository, plan.repository),
        ("issue_number", execution.issue_number, plan.issue_number),
        ("project_id", execution.project_id, plan.project_id),
        ("project_item_id", execution.project_item_id, plan.project_item_id),
    )
    for label, actual, expected in identity_pairs:
        if actual != expected:
            issues.append(f"execution {label} differs from the r5 plan")
    return tuple(dict.fromkeys(issues))


def _normalize_field_values(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(
                "projectv2_field_values must contain (name, value) tuples"
            )
        name, value = item
        if not isinstance(name, str) or not name.strip():
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                "ProjectV2 readback field names must be non-empty"
            )
        if not isinstance(value, str):
            raise TypeError("ProjectV2 readback field values must be strings")
        if name in normalized:
            raise SpecialistCapabilityGrowthProjectsReadbackError(
                f"duplicate ProjectV2 readback field: {name}"
            )
        normalized[name] = value
    return tuple(sorted(normalized.items()))


def _readback_digest(
    *,
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    execution: SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
    source_mode: str,
    matched_comment: SpecialistCapabilityGrowthIssueCommentReadback | None,
    actual_comment_digest: str,
    actual_field_values: Sequence[tuple[str, str]],
    issues: Sequence[str],
) -> str:
    payload = {
        "schema": SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA,
        "source_mode": source_mode,
        "repository": plan.repository,
        "issue_number": plan.issue_number,
        "project_id": plan.project_id,
        "project_item_id": plan.project_item_id,
        "plan_digest": plan.plan_digest,
        "execution_action": execution.action,
        "comment_id": (
            matched_comment.comment_id if matched_comment is not None else None
        ),
        "comment_body_sha256": actual_comment_digest,
        "projectv2_field_values": dict(actual_field_values),
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
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_VERSION",
    "SpecialistCapabilityGrowthIssueCommentReadback",
    "SpecialistCapabilityGrowthProjectsReadbackCommand",
    "SpecialistCapabilityGrowthProjectsReadbackError",
    "SpecialistCapabilityGrowthProjectsReadbackEvidence",
    "verify_specialist_capability_growth_projects_readback",
)
