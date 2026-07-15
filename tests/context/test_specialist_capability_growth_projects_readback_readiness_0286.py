from __future__ import annotations

from hashlib import sha256

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA,
    SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
)
from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
    SpecialistCapabilityGrowthProjectV2FieldMutation,
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)
from context.specialist_capability_growth_projects_readback_readiness_0286 import (
    SpecialistCapabilityGrowthIssueCommentReadback,
    SpecialistCapabilityGrowthProjectsReadbackCommand,
    verify_specialist_capability_growth_projects_readback,
)

FIELDS = (
    ("Spécialiste", "specialist:demo"),
    ("Révision spécialiste", "revision:2"),
    ("Capacité proposée", "technical_review"),
    ("Action capacité", "add"),
    ("Décision capacité", "approve"),
    ("Statut révision", "approved_selected_observed"),
    ("Référence SQL", "sql:revision:2"),
    ("Digest décision", "d" * 64),
    ("Laboratoire", "laboratory:fake-local"),
)


def _plan() -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    marker = "autodoc:specialist-capability-growth:fixture"
    body = (
        "<!-- " + marker + " -->\n"
        "approved specialist capability revision"
    )
    mutations = tuple(
        SpecialistCapabilityGrowthProjectV2FieldMutation(
            field_name=name,
            desired_value=value,
            current_value=None,
            action="set",
        )
        for name, value in FIELDS
    )
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
        valid=True,
        action="create_comment_and_set_fields",
        issues=(),
        repository="newicody/projects",
        issue_number=42,
        project_id="PVT_project3",
        project_item_id="PVTI_item42",
        policy_decision_id="policy:0286:r5:publish",
        review_ref="review:42",
        revision_ref="revision:2",
        sql_ref="sql:revision:2",
        decision_ref="decision:2",
        projection_digest_sha256="a" * 64,
        marker=marker,
        comment_action="create",
        comment_body=body,
        comment_body_sha256=sha256(body.encode("utf-8")).hexdigest(),
        existing_comment_id=None,
        existing_comment_url="",
        projectv2_action="set",
        projectv2_field_mutations=mutations,
        plan_digest="c" * 64,
    )


def _execution(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
) -> SpecialistCapabilityGrowthProjectsOperatorExecutionResult:
    return SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=(
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA
        ),
        valid=True,
        mode="execute",
        action="executed",
        issues=(),
        plan_digest=plan.plan_digest,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        comment_action="created",
        comment_id=99,
        comment_url="https://github.example/comment/99",
        projectv2_action="updated",
        changed_fields=tuple(name for name, _value in FIELDS),
        operator_decision="approve",
        confirmed_plan_digest=plan.plan_digest,
        remote_mutation_allowed=True,
        github_mutation_performed=True,
        issue_comment_published=True,
        projectv2_mutation_performed=True,
    )


def _command(
    *,
    source_mode: str = "provided_snapshots",
    comments: tuple[
        SpecialistCapabilityGrowthIssueCommentReadback, ...
    ] | None = None,
    fields: tuple[tuple[str, str], ...] = FIELDS,
) -> SpecialistCapabilityGrowthProjectsReadbackCommand:
    plan = _plan()
    return SpecialistCapabilityGrowthProjectsReadbackCommand(
        publication_plan=plan,
        execution_result=_execution(plan),
        issue_comments=comments
        if comments is not None
        else (
            SpecialistCapabilityGrowthIssueCommentReadback(
                comment_id=99,
                body=plan.comment_body,
                html_url="https://github.example/comment/99",
            ),
        ),
        projectv2_field_values=fields,
        source_mode=source_mode,
    )


def test_snapshot_readback_is_valid_but_not_deployment_ready() -> None:
    evidence = verify_specialist_capability_growth_projects_readback(
        _command()
    )
    assert evidence.valid is True
    assert evidence.action == "snapshot_ready"
    assert evidence.readback_ready is True
    assert evidence.deployment_ready is False
    assert evidence.remote_query_performed is False


def test_live_query_only_readback_can_be_deployment_ready() -> None:
    evidence = verify_specialist_capability_growth_projects_readback(
        _command(source_mode="live_query_only")
    )
    assert evidence.valid is True
    assert evidence.action == "deployment_ready"
    assert evidence.deployment_ready is True
    assert evidence.remote_query_performed is True
    assert evidence.remote_mutation_allowed is False


def test_missing_marked_comment_is_detected() -> None:
    evidence = verify_specialist_capability_growth_projects_readback(
        _command(comments=())
    )
    assert evidence.valid is False
    assert evidence.action == "drift_detected"
    assert "idempotency marker" in evidence.issues[0]


def test_duplicate_marked_comments_are_a_collision() -> None:
    plan = _plan()
    comment = SpecialistCapabilityGrowthIssueCommentReadback(
        comment_id=99, body=plan.comment_body
    )
    evidence = verify_specialist_capability_growth_projects_readback(
        _command(comments=(comment, comment))
    )
    assert evidence.valid is False
    assert any("multiple comments" in item for item in evidence.issues)


def test_projectv2_field_drift_is_detected() -> None:
    drifted = tuple(
        (name, "reject" if name == "Décision capacité" else value)
        for name, value in FIELDS
    )
    evidence = verify_specialist_capability_growth_projects_readback(
        _command(fields=drifted)
    )
    assert evidence.valid is False
    assert any("Décision capacité" in item for item in evidence.issues)


def test_execution_digest_mismatch_is_detected() -> None:
    plan = _plan()
    execution = _execution(plan)
    wrong = SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=execution.schema,
        valid=True,
        mode="execute",
        action="executed",
        issues=(),
        plan_digest="e" * 64,
        repository=execution.repository,
        issue_number=execution.issue_number,
        project_id=execution.project_id,
        project_item_id=execution.project_item_id,
        comment_action=execution.comment_action,
        comment_id=execution.comment_id,
        comment_url=execution.comment_url,
        projectv2_action=execution.projectv2_action,
        changed_fields=execution.changed_fields,
        operator_decision=execution.operator_decision,
        confirmed_plan_digest="e" * 64,
        remote_mutation_allowed=True,
        github_mutation_performed=True,
        issue_comment_published=True,
        projectv2_mutation_performed=True,
    )
    command = SpecialistCapabilityGrowthProjectsReadbackCommand(
        publication_plan=plan,
        execution_result=wrong,
        issue_comments=(
            SpecialistCapabilityGrowthIssueCommentReadback(
                comment_id=99, body=plan.comment_body
            ),
        ),
        projectv2_field_values=FIELDS,
    )
    evidence = verify_specialist_capability_growth_projects_readback(
        command
    )
    assert evidence.valid is False
    assert evidence.publication_execution_verified is False


def test_mapping_preserves_query_only_authority_split() -> None:
    mapping = verify_specialist_capability_growth_projects_readback(
        _command()
    ).to_mapping()
    assert mapping["query_only"] is True
    assert mapping["remote_mutation_allowed"] is False
    assert mapping["github_projects_authoritative"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
