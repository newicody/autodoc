from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest

from context.specialist_capability_growth_projects_publication_plan_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_COMMENT_MARKER_PREFIX,
    SpecialistCapabilityGrowthProjectsPublicationCommand,
    SpecialistCapabilityGrowthProjectsPublicationPlanError,
    plan_specialist_capability_growth_projects_publication,
)
from context.specialist_capability_growth_projects_review_projection_0286 import (
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA,
    SpecialistCapabilityGrowthProjectsReviewProjection,
)


DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64
DIGEST_F = "f" * 64


@dataclass(frozen=True, slots=True)
class CommentSnapshot:
    comment_id: int
    body: str
    html_url: str = ""


def _projection() -> SpecialistCapabilityGrowthProjectsReviewProjection:
    return SpecialistCapabilityGrowthProjectsReviewProjection(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA,
        review_ref="projects-review:0286-r2:technical",
        source_smoke_ref="smoke:0285-r8:technical",
        source_smoke_digest_sha256=DIGEST_A,
        proposal_ref="proposal:technical:2",
        proposal_digest_sha256=DIGEST_B,
        specialist_ref="specialist:technical",
        specialist_version="1.1.0",
        revision_ref="revision:technical:2",
        revision_digest_sha256=DIGEST_C,
        capability="technical-analysis",
        action="add",
        evidence_refs=("evidence:technical:1",),
        decision_ref="decision:technical:2",
        decision_digest_sha256=DIGEST_D,
        decision_outcome="approve",
        operator_ref="operator:eric",
        decision_reason="approved after local review",
        history_ref="history:technical",
        history_entry_ref="history-entry:technical:2",
        history_entry_digest_sha256=DIGEST_E,
        history_snapshot_digest_sha256=DIGEST_F,
        sql_ref="sql:specialist-history:technical:2",
        selection_ref="selection:technical:2",
        selection_digest_sha256=DIGEST_A,
        scheduler_ref="scheduler:main",
        laboratory_ref="laboratory:local-fake",
        visit_mode="execute",
        execution_boundary="local-deterministic",
        observation_event_id="event:technical:2",
        conversation_ref="conversation:technical:2",
        context_refs=("context:technical:2", "sql:context:technical:2"),
    )


def _command(**changes: object) -> SpecialistCapabilityGrowthProjectsPublicationCommand:
    values: dict[str, object] = {
        "repository": "newicody/projects",
        "issue_number": 42,
        "project_id": "PVT_project3",
        "project_item_id": "PVTI_item42",
        "policy_decision_id": "policy:0286:r5:publish",
        "operator_decision": "approve",
        "review_projection": _projection(),
    }
    values.update(changes)
    return SpecialistCapabilityGrowthProjectsPublicationCommand(**values)  # type: ignore[arg-type]


def test_builds_create_comment_and_set_fields_plan() -> None:
    plan = plan_specialist_capability_growth_projects_publication(_command())

    assert plan.valid is True
    assert plan.action == "create_comment_and_set_fields"
    assert plan.comment_action == "create"
    assert plan.projectv2_action == "set"
    assert len(plan.projectv2_field_changes) == 9
    assert plan.marker.startswith(SPECIALIST_CAPABILITY_GROWTH_COMMENT_MARKER_PREFIX)
    assert "SQL conserve l’historique durable" in plan.comment_body


def test_plan_preserves_revision_sql_and_decision_correlation() -> None:
    plan = plan_specialist_capability_growth_projects_publication(_command())

    assert plan.review_ref == "projects-review:0286-r2:technical"
    assert plan.revision_ref == "revision:technical:2"
    assert plan.sql_ref == "sql:specialist-history:technical:2"
    assert plan.decision_ref == "decision:technical:2"
    assert plan.projection_digest_sha256 == _projection().projection_digest


def test_only_the_nine_r4_projectv2_fields_are_planned() -> None:
    plan = plan_specialist_capability_growth_projects_publication(_command())
    fields = dict(plan.projectv2_field_values)

    assert tuple(fields) == (
        "Spécialiste",
        "Révision spécialiste",
        "Capacité proposée",
        "Action capacité",
        "Décision capacité",
        "Statut révision",
        "Référence SQL",
        "Digest décision",
        "Laboratoire",
    )
    assert fields["Révision spécialiste"] == "revision:technical:2"
    assert fields["Décision capacité"] == "approve"


def test_plan_digest_is_deterministic() -> None:
    left = plan_specialist_capability_growth_projects_publication(_command())
    right = plan_specialist_capability_growth_projects_publication(_command())

    assert left.plan_digest == right.plan_digest
    assert len(left.plan_digest) == 64


def test_identical_existing_comment_and_fields_are_replayed() -> None:
    initial = plan_specialist_capability_growth_projects_publication(_command())
    existing_fields = initial.projectv2_field_values
    replay = plan_specialist_capability_growth_projects_publication(
        _command(
            existing_comments=(
                CommentSnapshot(7, initial.comment_body, "https://example/comment/7"),
            ),
            existing_projectv2_field_values=existing_fields,
        )
    )

    assert replay.valid is True
    assert replay.action == "replay"
    assert replay.comment_action == "replay"
    assert replay.projectv2_action == "replay"
    assert replay.existing_comment_id == 7
    assert not replay.projectv2_field_changes


def test_identical_comment_with_stale_fields_only_sets_fields() -> None:
    initial = plan_specialist_capability_growth_projects_publication(_command())
    plan = plan_specialist_capability_growth_projects_publication(
        _command(existing_comments=(CommentSnapshot(7, initial.comment_body),))
    )

    assert plan.valid is True
    assert plan.action == "set_fields"
    assert plan.comment_action == "replay"
    assert len(plan.projectv2_field_changes) == 9


def test_new_comment_with_matching_fields_only_creates_comment() -> None:
    initial = plan_specialist_capability_growth_projects_publication(_command())
    plan = plan_specialist_capability_growth_projects_publication(
        _command(existing_projectv2_field_values=initial.projectv2_field_values)
    )

    assert plan.valid is True
    assert plan.action == "create_comment"
    assert plan.projectv2_action == "replay"


def test_changed_marked_comment_is_a_collision_and_blocks_fields() -> None:
    initial = plan_specialist_capability_growth_projects_publication(_command())
    collision_body = initial.comment_body.replace(
        "Révision approuvée",
        "Révision modifiée",
    )
    plan = plan_specialist_capability_growth_projects_publication(
        _command(existing_comments=(CommentSnapshot(7, collision_body),))
    )

    assert plan.valid is False
    assert plan.action == "collision"
    assert plan.comment_action == "collision"
    assert plan.projectv2_action == "blocked"
    assert "differs" in plan.issues[0]


def test_multiple_marked_comments_are_a_collision() -> None:
    initial = plan_specialist_capability_growth_projects_publication(_command())
    plan = plan_specialist_capability_growth_projects_publication(
        _command(
            existing_comments=(
                CommentSnapshot(7, initial.comment_body),
                CommentSnapshot(8, initial.comment_body),
            )
        )
    )

    assert plan.valid is False
    assert plan.action == "collision"
    assert "multiple existing comments" in plan.issues[0]


def test_partial_existing_fields_only_plan_missing_or_changed_values() -> None:
    plan = plan_specialist_capability_growth_projects_publication(
        _command(
            existing_projectv2_field_values=(
                ("Spécialiste", "specialist:technical"),
                ("Décision capacité", "pending"),
            )
        )
    )
    changes = {item.field_name: item for item in plan.projectv2_field_changes}

    assert "Spécialiste" not in changes
    assert changes["Décision capacité"].current_value == "pending"
    assert changes["Décision capacité"].desired_value == "approve"


def test_mapping_preserves_all_authority_boundaries() -> None:
    mapping = plan_specialist_capability_growth_projects_publication(
        _command()
    ).to_mapping()

    assert mapping["remote_mutation_allowed"] is False
    assert mapping["github_mutation_performed"] is False
    assert mapping["issue_comment_published"] is False
    assert mapping["projectv2_mutation_performed"] is False
    assert mapping["github_projects_authoritative"] is False
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_authoritative"] is False
    assert mapping["new_http_client_created"] is False


def test_command_and_plan_are_immutable() -> None:
    command = _command()
    plan = plan_specialist_capability_growth_projects_publication(command)

    with pytest.raises(FrozenInstanceError):
        command.issue_number = 9
    with pytest.raises(FrozenInstanceError):
        plan.action = "replay"


def test_non_approved_operator_intent_is_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProjectsPublicationPlanError,
        match="operator_decision",
    ):
        _command(operator_decision="defer")


def test_unexpected_existing_project_field_is_rejected() -> None:
    with pytest.raises(
        SpecialistCapabilityGrowthProjectsPublicationPlanError,
        match="unexpected existing ProjectV2 field",
    ):
        _command(existing_projectv2_field_values=(("Résumé", "forbidden"),))


def test_mandatory_comment_is_bounded() -> None:
    plan = plan_specialist_capability_growth_projects_publication(
        _command(max_comment_chars=2_000)
    )

    assert len(plan.comment_body) <= 2_000
    assert plan.marker in plan.comment_body
