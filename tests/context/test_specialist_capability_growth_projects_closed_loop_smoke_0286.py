from __future__ import annotations

from hashlib import sha256

from context.specialist_capability_growth_projects_closed_loop_smoke_0286 import (
    SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand,
    run_specialist_capability_growth_projects_closed_loop_smoke,
)
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
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA,
    SpecialistCapabilityGrowthProjectsReadbackEvidence,
)

FIELDS = (
    ("Spécialiste", "specialist:fixture"),
    ("Révision spécialiste", "revision:fixture:2"),
    ("Capacité proposée", "technical_review"),
    ("Action capacité", "add"),
    ("Décision capacité", "approve"),
    ("Statut révision", "approved_selected_observed"),
    ("Référence SQL", "sql:fixture:revision:2"),
    ("Digest décision", "d" * 64),
    ("Laboratoire", "laboratory:fixture-local"),
)


def _plan() -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    marker = "autodoc:specialist-capability-growth:fixture"
    body = f"<!-- {marker} -->\nclosed-loop fixture\n"
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=(
            SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA
        ),
        valid=True,
        action="replay",
        issues=(),
        repository="newicody/projects",
        issue_number=1,
        project_id="PVT_fixture",
        project_item_id="PVTI_fixture",
        policy_decision_id="policy:0286:r8:fixture",
        review_ref="projects-review:fixture",
        revision_ref="revision:fixture:2",
        sql_ref="sql:fixture:revision:2",
        decision_ref="decision:fixture:2",
        projection_digest_sha256="a" * 64,
        marker=marker,
        comment_action="replay",
        comment_body=body,
        comment_body_sha256=sha256(body.encode("utf-8")).hexdigest(),
        existing_comment_id=999_999,
        existing_comment_url="https://example.invalid/comment",
        projectv2_action="replay",
        projectv2_field_mutations=tuple(
            SpecialistCapabilityGrowthProjectV2FieldMutation(
                field_name=name,
                desired_value=value,
                current_value=value,
                action="replay",
            )
            for name, value in FIELDS
        ),
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
        action="replayed",
        issues=(),
        plan_digest=plan.plan_digest,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        comment_action="replayed",
        comment_id=plan.existing_comment_id,
        comment_url=plan.existing_comment_url,
        projectv2_action="replayed",
        changed_fields=(),
        operator_decision="approve",
        confirmed_plan_digest=plan.plan_digest,
        remote_mutation_allowed=True,
        github_mutation_performed=False,
        issue_comment_published=False,
        projectv2_mutation_performed=False,
    )


def _readback(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
    *,
    live: bool = False,
    fields: tuple[tuple[str, str], ...] = FIELDS,
) -> SpecialistCapabilityGrowthProjectsReadbackEvidence:
    source_mode = "live_query_only" if live else "provided_snapshots"
    return SpecialistCapabilityGrowthProjectsReadbackEvidence(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA,
        valid=True,
        action="deployment_ready" if live else "snapshot_ready",
        issues=(),
        source_mode=source_mode,
        repository=plan.repository,
        issue_number=plan.issue_number,
        project_id=plan.project_id,
        project_item_id=plan.project_item_id,
        plan_digest=plan.plan_digest,
        marker=plan.marker,
        sql_ref=plan.sql_ref,
        revision_ref=plan.revision_ref,
        decision_ref=plan.decision_ref,
        matched_comment_id=plan.existing_comment_id,
        matched_comment_url=plan.existing_comment_url,
        comment_body_sha256=plan.comment_body_sha256,
        expected_projectv2_field_values=FIELDS,
        actual_projectv2_field_values=fields,
        publication_execution_verified=True,
        issue_comment_verified=True,
        projectv2_fields_verified=True,
        readback_ready=True,
        deployment_ready=live,
        readback_digest="b" * 64,
        remote_query_performed=live,
    )


def test_local_fixture_closes_the_contract_not_the_deployment() -> None:
    plan = _plan()
    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=_execution(plan),
            readback_evidence=_readback(plan),
        )
    )
    assert result.valid is True
    assert result.action == "local_contract_closed"
    assert result.phase_0286_closed is True
    assert result.local_contract_closed is True
    assert result.deployment_closed is False
    assert result.remote_query_performed is False


def test_live_query_only_readback_closes_the_deployment() -> None:
    plan = _plan()
    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=_execution(plan),
            readback_evidence=_readback(plan, live=True),
            require_live_readback=True,
        )
    )
    assert result.valid is True
    assert result.action == "deployment_closed"
    assert result.phase_0286_closed is True
    assert result.deployment_closed is True
    assert result.remote_query_performed is True


def test_live_requirement_blocks_a_local_fixture() -> None:
    plan = _plan()
    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=_execution(plan),
            readback_evidence=_readback(plan),
            require_live_readback=True,
        )
    )
    assert result.valid is False
    assert result.action == "blocked"
    assert result.phase_0286_closed is False
    assert result.deployment_closed is False
    assert any("live query-only" in item for item in result.issues)


def test_wrong_execution_digest_is_detected() -> None:
    plan = _plan()
    execution = _execution(plan)
    wrong = SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=execution.schema,
        valid=True,
        mode="execute",
        action="replayed",
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
        github_mutation_performed=False,
        issue_comment_published=False,
        projectv2_mutation_performed=False,
    )
    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=wrong,
            readback_evidence=_readback(plan),
        )
    )
    assert result.valid is False
    assert result.plan_execution_correlated is False


def test_field_drift_is_detected_even_if_readback_flags_are_incorrect() -> None:
    plan = _plan()
    drifted_fields = tuple(
        (name, "reject" if name == "Décision capacité" else value)
        for name, value in FIELDS
    )
    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=_execution(plan),
            readback_evidence=_readback(plan, fields=drifted_fields),
        )
    )
    assert result.valid is False
    assert result.projectv2_fields_correlated is False


def test_mapping_locks_all_authority_boundaries() -> None:
    plan = _plan()
    mapping = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=plan,
            execution_result=_execution(plan),
            readback_evidence=_readback(plan),
        )
    ).to_mapping()
    assert mapping["remote_mutation_allowed"] is False
    assert mapping["github_mutation_performed_by_smoke"] is False
    assert mapping["sql_write_performed_by_smoke"] is False
    assert mapping["qdrant_write_performed_by_smoke"] is False
    assert mapping["scheduler_dispatch_performed_by_smoke"] is False
    assert mapping["github_projects_authoritative"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
