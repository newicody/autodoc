"""Operator-authorized adapter for capability-growth GitHub publication.

Phase 0286-r6 consumes the immutable r5 publication plan and delegates the
bounded remote effects to an existing GitHub execution boundary supplied
through a structural port.  This module creates no HTTP client and performs no
network access by itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)

SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA = (
    "missipy.specialist.capability_growth.projects_operator_adapter.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_VERSION = "0286.r6"


class SpecialistCapabilityGrowthProjectsOperatorAdapterError(ValueError):
    """Raised when remote execution is not explicitly authorized."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthCommentExecution:
    """Result returned by the existing Issue-comment boundary."""

    action: str
    comment_id: int | None = None
    comment_url: str = ""

    def __post_init__(self) -> None:
        if self.action not in {"created", "replayed"}:
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "comment execution action must be created or replayed"
            )
        if self.action == "created" and (
            not isinstance(self.comment_id, int) or self.comment_id <= 0
        ):
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "created comments require a positive comment_id"
            )


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectV2Execution:
    """Result returned by the existing ProjectV2 mutation boundary."""

    action: str
    changed_fields: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.action not in {"updated", "replayed"}:
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "ProjectV2 execution action must be updated or replayed"
            )
        object.__setattr__(self, "changed_fields", tuple(self.changed_fields))
        if self.action == "replayed" and self.changed_fields:
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "replayed ProjectV2 execution cannot report changed fields"
            )


@runtime_checkable
class SpecialistCapabilityGrowthGitHubExecutionPort(Protocol):
    """Structural port implemented by the existing GitHub/gh boundary."""

    def publish_issue_comment(
        self,
        *,
        repository: str,
        issue_number: int,
        body: str,
        marker: str,
    ) -> SpecialistCapabilityGrowthCommentExecution:
        """Create or replay the append-only Issue comment."""

    def apply_projectv2_fields(
        self,
        *,
        project_id: str,
        project_item_id: str,
        field_values: tuple[tuple[str, str], ...],
    ) -> SpecialistCapabilityGrowthProjectV2Execution:
        """Set or replay the bounded ProjectV2 field values."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsOperatorExecutionCommand:
    """Explicit local authorization for one exact r5 plan."""

    plan: SpecialistCapabilityGrowthProjectsPublicationPlan
    operator_decision: str
    execute: bool = False
    confirmed_plan_digest: str = ""

    def __post_init__(self) -> None:
        if not isinstance(
            self.plan, SpecialistCapabilityGrowthProjectsPublicationPlan
        ):
            raise TypeError("plan must be a r5 publication plan")
        if self.operator_decision not in {"approve", "reject", "defer"}:
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "unsupported operator decision"
            )


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsOperatorExecutionResult:
    """Bounded evidence returned after preview or authorized execution."""

    schema: str
    valid: bool
    mode: str
    action: str
    issues: tuple[str, ...]
    plan_digest: str
    repository: str
    issue_number: int
    project_id: str
    project_item_id: str
    comment_action: str
    comment_id: int | None
    comment_url: str
    projectv2_action: str
    changed_fields: tuple[str, ...]
    operator_decision: str
    confirmed_plan_digest: str
    remote_mutation_allowed: bool
    github_mutation_performed: bool
    issue_comment_published: bool
    projectv2_mutation_performed: bool
    github_projects_authoritative: bool = field(default=False, init=False)
    sql_remains_durable_authority: bool = field(default=True, init=False)
    scheduler_remains_only_orchestrator: bool = field(default=True, init=False)
    qdrant_authoritative: bool = field(default=False, init=False)
    new_http_client_created: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != (
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA
        ):
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "unsupported operator adapter schema"
            )
        if self.mode not in {"preview", "execute", "blocked"}:
            raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
                "unsupported execution mode"
            )
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "changed_fields", tuple(self.changed_fields))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "mode": self.mode,
            "action": self.action,
            "issues": list(self.issues),
            "plan_digest": self.plan_digest,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "project_id": self.project_id,
            "project_item_id": self.project_item_id,
            "comment_action": self.comment_action,
            "comment_id": self.comment_id,
            "comment_url": self.comment_url,
            "projectv2_action": self.projectv2_action,
            "changed_fields": list(self.changed_fields),
            "operator_decision": self.operator_decision,
            "confirmed_plan_digest": self.confirmed_plan_digest,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "github_mutation_performed": self.github_mutation_performed,
            "issue_comment_published": self.issue_comment_published,
            "projectv2_mutation_performed": self.projectv2_mutation_performed,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "new_http_client_created": False,
        }


def execute_specialist_capability_growth_projects_publication(
    command: SpecialistCapabilityGrowthProjectsOperatorExecutionCommand,
    *,
    port: SpecialistCapabilityGrowthGitHubExecutionPort | None = None,
) -> SpecialistCapabilityGrowthProjectsOperatorExecutionResult:
    """Preview by default or execute one exact, approved and confirmed plan."""

    plan = command.plan
    issues: list[str] = []

    if not plan.valid:
        issues.append("publication plan is not valid")
    if plan.action in {"collision", "blocked"}:
        issues.append("publication plan is blocked")
    if command.operator_decision != "approve":
        issues.append("operator decision must be approve")

    if not command.execute:
        return _result(
            command,
            valid=not issues,
            mode="preview" if not issues else "blocked",
            action="preview" if not issues else "blocked",
            issues=issues,
            remote_mutation_allowed=False,
        )

    if command.confirmed_plan_digest != plan.plan_digest:
        issues.append("confirmed plan digest does not match the publication plan")
    if port is None:
        issues.append("execution requires the existing GitHub execution port")
    elif not isinstance(port, SpecialistCapabilityGrowthGitHubExecutionPort):
        issues.append("port does not implement the GitHub execution boundary")

    if issues:
        return _result(
            command,
            valid=False,
            mode="blocked",
            action="blocked",
            issues=issues,
            remote_mutation_allowed=False,
        )

    assert port is not None
    comment_execution: SpecialistCapabilityGrowthCommentExecution | None = None
    fields_execution: SpecialistCapabilityGrowthProjectV2Execution | None = None

    if plan.comment_action == "create":
        comment_execution = port.publish_issue_comment(
            repository=plan.repository,
            issue_number=plan.issue_number,
            body=plan.comment_body,
            marker=plan.marker,
        )
    elif plan.comment_action == "replay":
        comment_execution = SpecialistCapabilityGrowthCommentExecution(
            action="replayed",
            comment_id=plan.existing_comment_id,
            comment_url=plan.existing_comment_url,
        )
    else:
        raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
            "unexpected comment action at execution boundary"
        )

    if plan.projectv2_action == "set":
        fields_execution = port.apply_projectv2_fields(
            project_id=plan.project_id,
            project_item_id=plan.project_item_id,
            field_values=tuple(
                (item.field_name, item.desired_value)
                for item in plan.projectv2_field_changes
            ),
        )
    elif plan.projectv2_action == "replay":
        fields_execution = SpecialistCapabilityGrowthProjectV2Execution(
            action="replayed"
        )
    else:
        raise SpecialistCapabilityGrowthProjectsOperatorAdapterError(
            "unexpected ProjectV2 action at execution boundary"
        )

    mutated = (
        comment_execution.action == "created"
        or fields_execution.action == "updated"
    )
    return _result(
        command,
        valid=True,
        mode="execute",
        action="executed" if mutated else "replayed",
        issues=(),
        comment_execution=comment_execution,
        fields_execution=fields_execution,
        remote_mutation_allowed=True,
        github_mutation_performed=mutated,
    )


def _result(
    command: SpecialistCapabilityGrowthProjectsOperatorExecutionCommand,
    *,
    valid: bool,
    mode: str,
    action: str,
    issues: tuple[str, ...] | list[str],
    comment_execution: SpecialistCapabilityGrowthCommentExecution | None = None,
    fields_execution: SpecialistCapabilityGrowthProjectV2Execution | None = None,
    remote_mutation_allowed: bool,
    github_mutation_performed: bool = False,
) -> SpecialistCapabilityGrowthProjectsOperatorExecutionResult:
    plan = command.plan
    return SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA,
        valid=valid,
        mode=mode,
        action=action,
        issues=tuple(dict.fromkeys(issues)),
        plan_digest=plan.plan_digest,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        comment_action=(
            comment_execution.action if comment_execution else plan.comment_action
        ),
        comment_id=(
            comment_execution.comment_id
            if comment_execution
            else plan.existing_comment_id
        ),
        comment_url=(
            comment_execution.comment_url
            if comment_execution
            else plan.existing_comment_url
        ),
        projectv2_action=(
            fields_execution.action if fields_execution else plan.projectv2_action
        ),
        changed_fields=(
            fields_execution.changed_fields if fields_execution else ()
        ),
        operator_decision=command.operator_decision,
        confirmed_plan_digest=command.confirmed_plan_digest,
        remote_mutation_allowed=remote_mutation_allowed,
        github_mutation_performed=github_mutation_performed,
        issue_comment_published=(
            comment_execution is not None
            and comment_execution.action == "created"
        ),
        projectv2_mutation_performed=(
            fields_execution is not None
            and fields_execution.action == "updated"
        ),
    )


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_VERSION",
    "SpecialistCapabilityGrowthCommentExecution",
    "SpecialistCapabilityGrowthGitHubExecutionPort",
    "SpecialistCapabilityGrowthProjectV2Execution",
    "SpecialistCapabilityGrowthProjectsOperatorAdapterError",
    "SpecialistCapabilityGrowthProjectsOperatorExecutionCommand",
    "SpecialistCapabilityGrowthProjectsOperatorExecutionResult",
    "execute_specialist_capability_growth_projects_publication",
)
