from __future__ import annotations

from dataclasses import dataclass

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (
    SpecialistCapabilityGrowthCommentExecution,
    SpecialistCapabilityGrowthProjectV2Execution,
    SpecialistCapabilityGrowthProjectsOperatorExecutionCommand,
    execute_specialist_capability_growth_projects_publication,
)
from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)


@dataclass
class FakePort:
    comments: int = 0
    fields: int = 0

    def publish_issue_comment(self, **kwargs: object) -> SpecialistCapabilityGrowthCommentExecution:
        self.comments += 1
        return SpecialistCapabilityGrowthCommentExecution(
            action="created", comment_id=17, comment_url="https://example/17"
        )

    def apply_projectv2_fields(self, **kwargs: object) -> SpecialistCapabilityGrowthProjectV2Execution:
        self.fields += 1
        values = kwargs["field_values"]
        return SpecialistCapabilityGrowthProjectV2Execution(
            action="updated",
            changed_fields=tuple(name for name, _value in values),  # type: ignore[arg-type]
        )


def _plan() -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    return SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema="missipy.specialist.capability_growth.projects_publication_plan.v1",
        valid=True,
        action="create_comment_and_set_fields",
        issues=(),
        repository="newicody/projects",
        issue_number=42,
        project_id="PVT_project3",
        project_item_id="PVTI_item42",
        policy_decision_id="policy:0286:r5:publish",
        review_ref="review:42",
        revision_ref="revision:42",
        sql_ref="sql:42",
        decision_ref="decision:42",
        projection_digest_sha256="a" * 64,
        marker="autodoc:specialist-capability-growth:abc",
        comment_action="create",
        comment_body="approved projection",
        comment_body_sha256="b" * 64,
        existing_comment_id=None,
        existing_comment_url="",
        projectv2_action="set",
        projectv2_field_mutations=(),
        plan_digest="c" * 64,
    )


def test_preview_is_default_and_does_not_call_port() -> None:
    port = FakePort()
    result = execute_specialist_capability_growth_projects_publication(
        SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
            plan=_plan(), operator_decision="approve"
        ),
        port=port,
    )
    assert result.valid is True
    assert result.mode == "preview"
    assert result.remote_mutation_allowed is False
    assert result.github_mutation_performed is False
    assert port.comments == 0
    assert port.fields == 0


def test_execute_requires_exact_digest() -> None:
    port = FakePort()
    result = execute_specialist_capability_growth_projects_publication(
        SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
            plan=_plan(),
            operator_decision="approve",
            execute=True,
            confirmed_plan_digest="d" * 64,
        ),
        port=port,
    )
    assert result.valid is False
    assert result.mode == "blocked"
    assert "digest" in result.issues[0]
    assert port.comments == 0


def test_reject_never_executes() -> None:
    port = FakePort()
    result = execute_specialist_capability_growth_projects_publication(
        SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
            plan=_plan(),
            operator_decision="reject",
            execute=True,
            confirmed_plan_digest="c" * 64,
        ),
        port=port,
    )
    assert result.valid is False
    assert result.remote_mutation_allowed is False
    assert port.comments == 0


def test_approved_confirmed_execution_delegates_to_existing_port() -> None:
    port = FakePort()
    result = execute_specialist_capability_growth_projects_publication(
        SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
            plan=_plan(),
            operator_decision="approve",
            execute=True,
            confirmed_plan_digest="c" * 64,
        ),
        port=port,
    )
    assert result.valid is True
    assert result.mode == "execute"
    assert result.action == "executed"
    assert result.comment_id == 17
    assert result.remote_mutation_allowed is True
    assert result.github_mutation_performed is True
    assert result.issue_comment_published is True
    assert port.comments == 1
    assert port.fields == 1


def test_mapping_preserves_authority_split() -> None:
    result = execute_specialist_capability_growth_projects_publication(
        SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
            plan=_plan(), operator_decision="approve"
        )
    )
    mapping = result.to_mapping()
    assert mapping["github_projects_authoritative"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["new_http_client_created"] is False
