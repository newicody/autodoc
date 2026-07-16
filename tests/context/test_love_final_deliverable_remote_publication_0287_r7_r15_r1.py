from __future__ import annotations

from dataclasses import replace
import hashlib

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.love_final_deliverable_publication_plan_0287 import (
    PROJECT_PROJECTION_SCHEMA,
    READBACK_EXPECTATION_SCHEMA,
    FinalDeliverableProjectV2Projection,
    FinalDeliverablePublicationOperation,
    FinalDeliverablePublicationReadbackExpectation,
    LoveFinalDeliverablePublicationPlan,
    ProjectV2FieldSnapshot,
)
from context.love_final_deliverable_remote_publication_0287 import (
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
    LoveFinalDeliverableRemotePublicationCommand,
    execute_love_final_deliverable_remote_publication,
    parse_love_final_deliverable_publication_plan,
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _plan() -> LoveFinalDeliverablePublicationPlan:
    marker = "autodoc:final-deliverable:0123456789abcdef01234567"
    body = f"<!-- {marker} -->\n\n## Autodoc — livrable final\n\nSynthèse.\n"
    value = "Livrable final prêt — Étude — final-artifact:love:1"
    projection = FinalDeliverableProjectV2Projection(
        schema=PROJECT_PROJECTION_SCHEMA,
        project_item_id="PVTI_test_item",
        field_ref="PVTF_test_field",
        field_name="Étape Status",
        value=value,
        value_sha256=_sha256(value),
        source_issue_ref="github-frame:newicody/projects/issues/41",
        final_ref="final:love:1",
        artifact_ref="final-artifact:love:1",
        synthesis_ref="synthesis:love:1",
    )
    return LoveFinalDeliverablePublicationPlan(
        valid=True,
        action="create_and_project",
        issue_action="create",
        project_action="update",
        issues=(),
        repository="newicody/projects",
        issue_number=41,
        source_issue_ref="github-frame:newicody/projects/issues/41",
        marker=marker,
        body=body,
        body_sha256=_sha256(body),
        plan_ref="github-final-deliverable-plan:0123456789abcdef01234567",
        plan_digest="a" * 64,
        project_projection=projection,
        operations=(
            FinalDeliverablePublicationOperation(
                kind="create_issue_comment",
                target_ref="github-frame:newicody/projects/issues/41",
                payload_sha256=_sha256(body),
            ),
            FinalDeliverablePublicationOperation(
                kind="update_project_v2_field",
                target_ref="github-project-v2-item:PVTI_test_item:PVTF_test_field",
                payload_sha256=_sha256(value),
                depends_on=("create_issue_comment",),
            ),
        ),
        readback_expectation=(
            FinalDeliverablePublicationReadbackExpectation(
                schema=READBACK_EXPECTATION_SCHEMA,
                marker=marker,
                body_sha256=_sha256(body),
                project_item_id="PVTI_test_item",
                project_field_ref="PVTF_test_field",
                project_value_sha256=_sha256(value),
            )
        ),
    )


class _IssuePort:
    def __init__(
        self,
        comments: tuple[GitHubIssueCommentSnapshot, ...] = (),
    ) -> None:
        self.comments = list(comments)
        self.create_calls = 0

    def list_comments(
        self,
        repository: str,
        issue_number: int,
    ) -> tuple[GitHubIssueCommentSnapshot, ...]:
        assert repository == "newicody/projects"
        assert issue_number == 41
        return tuple(self.comments)

    def create_comment(
        self,
        repository: str,
        issue_number: int,
        body: str,
    ) -> GitHubIssueCommentSnapshot:
        self.create_calls += 1
        comment = GitHubIssueCommentSnapshot(
            comment_id=900 + self.create_calls,
            body=body,
            html_url=f"https://github.com/{repository}/issues/{issue_number}#issuecomment-1",
        )
        self.comments.append(comment)
        return comment


class _ProjectPort:
    def __init__(
        self,
        snapshot: ProjectV2FieldSnapshot | None = None,
        *,
        fail_update: bool = False,
    ) -> None:
        self.snapshot = snapshot
        self.fail_update = fail_update
        self.update_calls = 0

    def read_field(
        self,
        *,
        project_item_id: str,
        field_ref: str,
        field_name: str,
    ) -> ProjectV2FieldSnapshot | None:
        return self.snapshot

    def update_field(
        self,
        projection: FinalDeliverableProjectV2Projection,
    ) -> None:
        self.update_calls += 1
        if self.fail_update:
            raise RuntimeError("project mutation failed")
        self.snapshot = ProjectV2FieldSnapshot(
            project_item_id=projection.project_item_id,
            field_ref=projection.field_ref,
            field_name=projection.field_name,
            value=projection.value,
        )


def _command(
    plan: LoveFinalDeliverablePublicationPlan,
    *,
    execute: bool = False,
    digest: str = "",
    locks: bool = False,
) -> LoveFinalDeliverableRemotePublicationCommand:
    return LoveFinalDeliverableRemotePublicationCommand(
        schema=LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
        plan=plan,
        operator_decision="approve",
        execute=execute,
        confirm_plan_digest=digest,
        remote_mutation_allowed=locks,
        issue_publication_allowed=locks,
        project_projection_allowed=locks,
    )


def _project_snapshot(plan: LoveFinalDeliverablePublicationPlan) -> ProjectV2FieldSnapshot:
    assert plan.project_projection is not None
    return ProjectV2FieldSnapshot(
        project_item_id=plan.project_projection.project_item_id,
        field_ref=plan.project_projection.field_ref,
        field_name=plan.project_projection.field_name,
        value=plan.project_projection.value,
    )


def test_preview_reads_both_surfaces_without_mutation() -> None:
    plan = _plan()
    issue = _IssuePort()
    project = _ProjectPort()

    result = execute_love_final_deliverable_remote_publication(
        _command(plan),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is True
    assert result.action == "preview"
    assert result.issue_action == "create"
    assert result.project_action == "update"
    assert result.remote_mutation_performed is False
    assert issue.create_calls == 0
    assert project.update_calls == 0


def test_execute_requires_exact_locks_and_confirms_remote_readback() -> None:
    plan = _plan()
    issue = _IssuePort()
    project = _ProjectPort()

    result = execute_love_final_deliverable_remote_publication(
        _command(plan, execute=True, digest=plan.plan_digest, locks=True),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is True
    assert result.action == "created_and_projected"
    assert result.issue_mutation_performed is True
    assert result.project_mutation_performed is True
    assert result.readback is not None
    assert result.readback.valid is True
    assert result.readback.plan_digest == plan.plan_digest
    assert issue.create_calls == 1
    assert project.update_calls == 1


def test_exact_existing_state_is_an_idempotent_replay() -> None:
    plan = _plan()
    issue = _IssuePort(
        (
            GitHubIssueCommentSnapshot(
                comment_id=77,
                body=plan.body,
                html_url="https://example.invalid/comment/77",
            ),
        )
    )
    project = _ProjectPort(_project_snapshot(plan))

    result = execute_love_final_deliverable_remote_publication(
        _command(plan, execute=True, digest=plan.plan_digest, locks=True),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is True
    assert result.action == "replay"
    assert result.issue_action == "replay"
    assert result.project_action == "replay"
    assert result.remote_mutation_performed is False
    assert result.readback is not None and result.readback.valid is True


def test_digest_mismatch_blocks_before_any_mutation() -> None:
    plan = _plan()
    issue = _IssuePort()
    project = _ProjectPort()

    result = execute_love_final_deliverable_remote_publication(
        _command(plan, execute=True, digest="b" * 64, locks=True),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is False
    assert result.action == "blocked"
    assert "confirm-plan-digest mismatch" in result.issues
    assert issue.create_calls == 0
    assert project.update_calls == 0


def test_changed_marked_comment_is_a_collision() -> None:
    plan = _plan()
    issue = _IssuePort(
        (
            GitHubIssueCommentSnapshot(
                comment_id=88,
                body=f"<!-- {plan.marker} -->\nchanged",
            ),
        )
    )
    project = _ProjectPort()

    result = execute_love_final_deliverable_remote_publication(
        _command(plan),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.issue_action == "collision"
    assert issue.create_calls == 0


def test_project_failure_after_issue_creation_is_reported_as_partial() -> None:
    plan = _plan()
    issue = _IssuePort()
    project = _ProjectPort(fail_update=True)

    result = execute_love_final_deliverable_remote_publication(
        _command(plan, execute=True, digest=plan.plan_digest, locks=True),
        issue_port=issue,
        project_port=project,
    )

    assert result.valid is False
    assert result.action == "partial"
    assert result.partial_execution is True
    assert result.issue_mutation_performed is True
    assert result.project_mutation_performed is False
    assert "project mutation failed" in result.execution_error


def test_project_identity_mismatch_is_a_collision() -> None:
    plan = _plan()
    project = _ProjectPort(
        replace(_project_snapshot(plan), field_ref="PVTF_other")
    )

    result = execute_love_final_deliverable_remote_publication(
        _command(plan),
        issue_port=_IssuePort(),
        project_port=project,
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.project_action == "collision"


def test_plan_parser_accepts_r13_mapping_and_nested_r14_mapping() -> None:
    plan = _plan()

    direct = parse_love_final_deliverable_publication_plan(plan.to_mapping())
    nested = parse_love_final_deliverable_publication_plan(
        {"publication_plan": plan.to_mapping()}
    )

    assert direct == plan
    assert nested == plan
