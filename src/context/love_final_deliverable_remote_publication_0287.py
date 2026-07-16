"""Controlled remote execution of an r13 final-deliverable publication plan.

The domain surface is deliberately transport-agnostic.  It consumes the exact
immutable plan produced by ``love_final_deliverable_publication_plan_0287`` and
uses injected Issue and ProjectV2 ports.  Preview is the default.  Execution
requires explicit operator approval, three mutation locks and the exact r13
``plan_digest``.  Exact Issue and ProjectV2 readback is delegated to the r13
verifier.

Network and subprocess code belong to the local adapter under ``tools``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.love_final_deliverable_publication_plan_0287 import (
    READBACK_EXPECTATION_SCHEMA,
    SCHEMA as PUBLICATION_PLAN_SCHEMA,
    FinalDeliverableProjectV2Projection,
    FinalDeliverablePublicationOperation,
    FinalDeliverablePublicationReadbackExpectation,
    FinalDeliverablePublicationReadbackResult,
    LoveFinalDeliverablePublicationPlan,
    ProjectV2FieldSnapshot,
    verify_love_final_deliverable_publication_readback,
)

LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA = (
    "missipy.love.final_deliverable_remote_publication_command.v1"
)
LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA = (
    "missipy.love.final_deliverable_remote_publication_result.v1"
)
_ALLOWED_OPERATOR_DECISIONS = frozenset({"approve"})


class FinalDeliverableIssuePublicationPort(Protocol):
    """Minimal Issue comment boundary required by the controlled executor."""

    def list_comments(
        self,
        repository: str,
        issue_number: int,
    ) -> tuple[GitHubIssueCommentSnapshot, ...]: ...

    def create_comment(
        self,
        repository: str,
        issue_number: int,
        body: str,
    ) -> GitHubIssueCommentSnapshot: ...


class FinalDeliverableProjectV2PublicationPort(Protocol):
    """Minimal ProjectV2 field boundary required by the controlled executor."""

    def read_field(
        self,
        *,
        project_item_id: str,
        field_ref: str,
        field_name: str,
    ) -> ProjectV2FieldSnapshot | None: ...

    def update_field(
        self,
        projection: FinalDeliverableProjectV2Projection,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class LoveFinalDeliverableRemotePublicationCommand:
    schema: str
    plan: LoveFinalDeliverablePublicationPlan
    operator_decision: str
    execute: bool = False
    confirm_plan_digest: str = ""
    remote_mutation_allowed: bool = False
    issue_publication_allowed: bool = False
    project_projection_allowed: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA:
            raise ValueError("unsupported remote publication command schema")
        if not isinstance(self.plan, LoveFinalDeliverablePublicationPlan):
            raise TypeError("plan must be LoveFinalDeliverablePublicationPlan")
        if self.operator_decision not in _ALLOWED_OPERATOR_DECISIONS:
            raise ValueError("operator_decision must be approve")
        if self.execute and not self.confirm_plan_digest:
            raise ValueError("execute requires confirm_plan_digest")


@dataclass(frozen=True, slots=True)
class LoveFinalDeliverableRemotePublicationResult:
    schema: str
    valid: bool
    mode: str
    action: str
    issues: tuple[str, ...]
    plan_digest: str
    issue_action: str
    project_action: str
    issue_comment_id: int | None = None
    issue_comment_url: str = ""
    project_snapshot: ProjectV2FieldSnapshot | None = None
    readback: FinalDeliverablePublicationReadbackResult | None = None
    issue_mutation_performed: bool = False
    project_mutation_performed: bool = False
    partial_execution: bool = False
    execution_error: str = ""
    existing_scheduler_used: bool = False
    scheduler_modified: bool = False
    sql_modified: bool = False
    qdrant_modified: bool = False
    openvino_modified: bool = False

    def __post_init__(self) -> None:
        if self.schema != LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA:
            raise ValueError("unsupported remote publication result schema")
        if self.mode not in {"preview", "execute"}:
            raise ValueError("mode must be preview or execute")
        if self.action not in {
            "preview",
            "created_and_projected",
            "created_issue",
            "projected",
            "replay",
            "blocked",
            "collision",
            "partial",
        }:
            raise ValueError("unsupported remote publication result action")
        if not isinstance(self.issues, tuple):
            object.__setattr__(self, "issues", tuple(self.issues))
        if self.valid and self.issues:
            raise ValueError("valid result cannot carry issues")
        if self.partial_execution != (
            self.action == "partial"
            or (
                self.issue_mutation_performed
                != self.project_mutation_performed
                and bool(self.execution_error)
            )
        ):
            raise ValueError("partial_execution does not match mutation outcome")
        if any(
            (
                self.existing_scheduler_used,
                self.scheduler_modified,
                self.sql_modified,
                self.qdrant_modified,
                self.openvino_modified,
            )
        ):
            raise ValueError("remote publication adapter changed a local authority")

    @property
    def remote_mutation_performed(self) -> bool:
        return self.issue_mutation_performed or self.project_mutation_performed

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "mode": self.mode,
            "action": self.action,
            "issues": list(self.issues),
            "plan_digest": self.plan_digest,
            "issue_action": self.issue_action,
            "project_action": self.project_action,
            "issue_comment_id": self.issue_comment_id,
            "issue_comment_url": self.issue_comment_url,
            "project_snapshot": (
                None
                if self.project_snapshot is None
                else self.project_snapshot.to_mapping()
            ),
            "readback": (
                None if self.readback is None else self.readback.to_mapping()
            ),
            "issue_mutation_performed": self.issue_mutation_performed,
            "project_mutation_performed": self.project_mutation_performed,
            "remote_mutation_performed": self.remote_mutation_performed,
            "partial_execution": self.partial_execution,
            "execution_error": self.execution_error,
            "boundaries": {
                "explicit_operator_authorization_required": True,
                "exact_plan_digest_confirmation_required": True,
                "remote_mutation_lock_required": True,
                "issue_publication_lock_required": True,
                "project_projection_lock_required": True,
                "preview_is_default": True,
                "collision_guarded": True,
                "exact_readback_required": True,
                "workflow_self_authorized": False,
                "existing_scheduler_used": False,
                "scheduler_modified": False,
                "sql_modified": False,
                "qdrant_modified": False,
                "openvino_modified": False,
            },
        }


def parse_love_final_deliverable_publication_plan(
    payload: Mapping[str, Any],
) -> LoveFinalDeliverablePublicationPlan:
    """Rehydrate the immutable r13 plan from its JSON mapping.

    ``payload`` may be the plan mapping itself or an r14 result mapping carrying
    the plan under ``publication_plan``.
    """

    raw = payload.get("publication_plan", payload)
    if not isinstance(raw, Mapping):
        raise ValueError("publication plan payload must be a JSON object")
    if raw.get("schema") != PUBLICATION_PLAN_SCHEMA:
        raise ValueError("unexpected final deliverable publication plan schema")

    projection_payload = raw.get("project_projection")
    projection = None
    if projection_payload is not None:
        projection_map = _mapping(projection_payload, "project_projection")
        projection = FinalDeliverableProjectV2Projection(
            schema=str(projection_map.get("schema", "")),
            project_item_id=str(projection_map.get("project_item_id", "")),
            field_ref=str(projection_map.get("field_ref", "")),
            field_name=str(projection_map.get("field_name", "")),
            value=str(projection_map.get("value", "")),
            value_sha256=str(projection_map.get("value_sha256", "")),
            source_issue_ref=str(projection_map.get("source_issue_ref", "")),
            final_ref=str(projection_map.get("final_ref", "")),
            artifact_ref=str(projection_map.get("artifact_ref", "")),
            synthesis_ref=str(projection_map.get("synthesis_ref", "")),
            readback_required=bool(
                projection_map.get("readback_required", False)
            ),
        )

    operations: list[FinalDeliverablePublicationOperation] = []
    for item in _sequence(raw.get("operations"), "operations"):
        operation = _mapping(item, "operation")
        operations.append(
            FinalDeliverablePublicationOperation(
                kind=str(operation.get("kind", "")),
                target_ref=str(operation.get("target_ref", "")),
                payload_sha256=str(operation.get("payload_sha256", "")),
                depends_on=tuple(
                    str(value)
                    for value in _sequence(
                        operation.get("depends_on", ()),
                        "operation.depends_on",
                    )
                ),
            )
        )

    expectation_payload = raw.get("readback_expectation")
    expectation = None
    if expectation_payload is not None:
        expectation_map = _mapping(
            expectation_payload,
            "readback_expectation",
        )
        expectation = FinalDeliverablePublicationReadbackExpectation(
            schema=str(
                expectation_map.get("schema", READBACK_EXPECTATION_SCHEMA)
            ),
            marker=str(expectation_map.get("marker", "")),
            body_sha256=str(expectation_map.get("body_sha256", "")),
            project_item_id=str(
                expectation_map.get("project_item_id", "")
            ),
            project_field_ref=str(
                expectation_map.get("project_field_ref", "")
            ),
            project_value_sha256=str(
                expectation_map.get("project_value_sha256", "")
            ),
            require_exact_issue_body=bool(
                expectation_map.get("require_exact_issue_body", False)
            ),
            require_exact_project_value=bool(
                expectation_map.get("require_exact_project_value", False)
            ),
        )

    return LoveFinalDeliverablePublicationPlan(
        valid=bool(raw.get("valid", False)),
        action=str(raw.get("action", "blocked")),
        issue_action=str(raw.get("issue_action", "blocked")),
        project_action=str(raw.get("project_action", "blocked")),
        issues=tuple(
            str(value)
            for value in _sequence(raw.get("issues", ()), "issues")
        ),
        repository=str(raw.get("repository", "")),
        issue_number=int(raw.get("issue_number", 0)),
        source_issue_ref=str(raw.get("source_issue_ref", "")),
        marker=str(raw.get("marker", "")),
        body=str(raw.get("body", "")),
        body_sha256=str(raw.get("body_sha256", "")),
        plan_ref=str(raw.get("plan_ref", "")),
        plan_digest=str(raw.get("plan_digest", "")),
        project_projection=projection,
        operations=tuple(operations),
        readback_expectation=expectation,
        existing_comment_id=(
            None
            if raw.get("existing_comment_id") is None
            else int(raw.get("existing_comment_id"))
        ),
        existing_comment_url=str(raw.get("existing_comment_url", "")),
    )


def execute_love_final_deliverable_remote_publication(
    command: LoveFinalDeliverableRemotePublicationCommand,
    *,
    issue_port: FinalDeliverableIssuePublicationPort,
    project_port: FinalDeliverableProjectV2PublicationPort,
) -> LoveFinalDeliverableRemotePublicationResult:
    """Preview or execute one exact r13 Issue + ProjectV2 publication plan."""

    plan = command.plan
    mode = "execute" if command.execute else "preview"
    if not plan.valid or plan.project_projection is None:
        return _result(
            command,
            valid=False,
            mode=mode,
            action="blocked",
            issue_action="blocked",
            project_action="blocked",
            issues=("r13 publication plan must be valid and complete",),
        )

    try:
        comments = issue_port.list_comments(plan.repository, plan.issue_number)
        project_snapshot = project_port.read_field(
            project_item_id=plan.project_projection.project_item_id,
            field_ref=plan.project_projection.field_ref,
            field_name=plan.project_projection.field_name,
        )
    except Exception as exc:
        return _result(
            command,
            valid=False,
            mode=mode,
            action="blocked",
            issue_action="blocked",
            project_action="blocked",
            issues=("remote preflight read failed",),
            execution_error=str(exc),
        )

    issue_action, matched_comment, issue_issues = _issue_action(plan, comments)
    project_action, project_issues = _project_action(plan, project_snapshot)
    preflight_issues = tuple((*issue_issues, *project_issues))
    if preflight_issues:
        return _result(
            command,
            valid=False,
            mode=mode,
            action=(
                "collision"
                if issue_action == "collision"
                or project_action == "collision"
                else "blocked"
            ),
            issue_action=issue_action,
            project_action=project_action,
            issues=preflight_issues,
            comment=matched_comment,
            project_snapshot=project_snapshot,
        )

    if not command.execute:
        return _result(
            command,
            valid=True,
            mode="preview",
            action="preview",
            issue_action=issue_action,
            project_action=project_action,
            issues=(),
            comment=matched_comment,
            project_snapshot=project_snapshot,
        )

    lock_issues = _execution_lock_issues(command)
    if lock_issues:
        return _result(
            command,
            valid=False,
            mode="execute",
            action="blocked",
            issue_action=issue_action,
            project_action=project_action,
            issues=lock_issues,
            comment=matched_comment,
            project_snapshot=project_snapshot,
        )

    issue_mutated = False
    project_mutated = False
    created_comment = matched_comment
    try:
        if issue_action == "create":
            created_comment = issue_port.create_comment(
                plan.repository,
                plan.issue_number,
                plan.body,
            )
            issue_mutated = True
        if project_action == "update":
            project_port.update_field(plan.project_projection)
            project_mutated = True
    except Exception as exc:
        return _result(
            command,
            valid=False,
            mode="execute",
            action="partial" if issue_mutated or project_mutated else "blocked",
            issue_action=issue_action,
            project_action=project_action,
            issues=("remote publication execution failed",),
            comment=created_comment,
            project_snapshot=project_snapshot,
            issue_mutated=issue_mutated,
            project_mutated=project_mutated,
            partial=issue_mutated or project_mutated,
            execution_error=str(exc),
        )

    try:
        readback_comments = issue_port.list_comments(
            plan.repository,
            plan.issue_number,
        )
        readback_project = project_port.read_field(
            project_item_id=plan.project_projection.project_item_id,
            field_ref=plan.project_projection.field_ref,
            field_name=plan.project_projection.field_name,
        )
        readback = verify_love_final_deliverable_publication_readback(
            plan,
            issue_comments=readback_comments,
            project_snapshot=readback_project,
        )
    except Exception as exc:
        return _result(
            command,
            valid=False,
            mode="execute",
            action="partial" if issue_mutated or project_mutated else "blocked",
            issue_action=issue_action,
            project_action=project_action,
            issues=("remote publication readback failed",),
            comment=created_comment,
            project_snapshot=project_snapshot,
            issue_mutated=issue_mutated,
            project_mutated=project_mutated,
            partial=issue_mutated or project_mutated,
            execution_error=str(exc),
        )

    if not readback.valid:
        return _result(
            command,
            valid=False,
            mode="execute",
            action="partial" if issue_mutated or project_mutated else "blocked",
            issue_action=issue_action,
            project_action=project_action,
            issues=readback.issues,
            comment=_matching_comment(plan, readback_comments),
            project_snapshot=readback_project,
            readback=readback,
            issue_mutated=issue_mutated,
            project_mutated=project_mutated,
            partial=issue_mutated or project_mutated,
        )

    return _result(
        command,
        valid=True,
        mode="execute",
        action=_completed_action(issue_mutated, project_mutated),
        issue_action=issue_action,
        project_action=project_action,
        issues=(),
        comment=_matching_comment(plan, readback_comments),
        project_snapshot=readback_project,
        readback=readback,
        issue_mutated=issue_mutated,
        project_mutated=project_mutated,
    )


def _execution_lock_issues(
    command: LoveFinalDeliverableRemotePublicationCommand,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not command.remote_mutation_allowed:
        issues.append("remote mutation lock is closed")
    if not command.issue_publication_allowed:
        issues.append("Issue publication lock is closed")
    if not command.project_projection_allowed:
        issues.append("ProjectV2 projection lock is closed")
    if command.confirm_plan_digest != command.plan.plan_digest:
        issues.append("confirm-plan-digest mismatch")
    return tuple(issues)


def _issue_action(
    plan: LoveFinalDeliverablePublicationPlan,
    comments: Sequence[GitHubIssueCommentSnapshot],
) -> tuple[str, GitHubIssueCommentSnapshot | None, tuple[str, ...]]:
    matches = tuple(comment for comment in comments if plan.marker in comment.body)
    if len(matches) > 1:
        return (
            "collision",
            None,
            ("multiple Issue comments carry the final deliverable marker",),
        )
    if not matches:
        return "create", None, ()
    comment = matches[0]
    if comment.body == plan.body:
        return "replay", comment, ()
    return (
        "collision",
        comment,
        ("existing final deliverable comment differs from approved body",),
    )


def _project_action(
    plan: LoveFinalDeliverablePublicationPlan,
    snapshot: ProjectV2FieldSnapshot | None,
) -> tuple[str, tuple[str, ...]]:
    projection = plan.project_projection
    if projection is None:
        return "blocked", ("ProjectV2 projection is absent",)
    if snapshot is None:
        return "update", ()
    if snapshot.project_item_id != projection.project_item_id:
        return "collision", ("ProjectV2 item identity mismatch",)
    if snapshot.field_ref != projection.field_ref:
        return "collision", ("ProjectV2 field identity mismatch",)
    if snapshot.field_name != projection.field_name:
        return "collision", ("ProjectV2 field name mismatch",)
    if snapshot.value == projection.value:
        return "replay", ()
    return "update", ()


def _matching_comment(
    plan: LoveFinalDeliverablePublicationPlan,
    comments: Sequence[GitHubIssueCommentSnapshot],
) -> GitHubIssueCommentSnapshot | None:
    matches = tuple(comment for comment in comments if plan.marker in comment.body)
    return matches[0] if len(matches) == 1 else None


def _completed_action(issue_mutated: bool, project_mutated: bool) -> str:
    if issue_mutated and project_mutated:
        return "created_and_projected"
    if issue_mutated:
        return "created_issue"
    if project_mutated:
        return "projected"
    return "replay"


def _result(
    command: LoveFinalDeliverableRemotePublicationCommand,
    *,
    valid: bool,
    mode: str,
    action: str,
    issue_action: str,
    project_action: str,
    issues: tuple[str, ...],
    comment: GitHubIssueCommentSnapshot | None = None,
    project_snapshot: ProjectV2FieldSnapshot | None = None,
    readback: FinalDeliverablePublicationReadbackResult | None = None,
    issue_mutated: bool = False,
    project_mutated: bool = False,
    partial: bool = False,
    execution_error: str = "",
) -> LoveFinalDeliverableRemotePublicationResult:
    return LoveFinalDeliverableRemotePublicationResult(
        schema=LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA,
        valid=valid,
        mode=mode,
        action=action,
        issues=tuple(dict.fromkeys(issues)),
        plan_digest=command.plan.plan_digest,
        issue_action=issue_action,
        project_action=project_action,
        issue_comment_id=None if comment is None else comment.comment_id,
        issue_comment_url="" if comment is None else comment.html_url,
        project_snapshot=project_snapshot,
        readback=readback,
        issue_mutation_performed=issue_mutated,
        project_mutation_performed=project_mutated,
        partial_execution=partial,
        execution_error=execution_error,
    )


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return value
    raise ValueError(f"{name} must be a JSON array")


__all__ = (
    "LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA",
    "LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_RESULT_SCHEMA",
    "FinalDeliverableIssuePublicationPort",
    "FinalDeliverableProjectV2PublicationPort",
    "LoveFinalDeliverableRemotePublicationCommand",
    "LoveFinalDeliverableRemotePublicationResult",
    "execute_love_final_deliverable_remote_publication",
    "parse_love_final_deliverable_publication_plan",
)
