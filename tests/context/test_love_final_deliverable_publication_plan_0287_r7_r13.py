from __future__ import annotations

from types import SimpleNamespace

import pytest

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.love_final_deliverable_publication_plan_0287 import (
    MARKER_PREFIX,
    LoveFinalDeliverablePublicationCommand,
    ProjectV2FieldSnapshot,
    plan_love_final_deliverable_publication,
    verify_love_final_deliverable_publication_readback,
)


def _result(*, github_mutation_performed: bool = False, ready: bool = True):
    envelope = SimpleNamespace(
        final_ref="final:love-study:001",
        target_ref="target:love-study:001",
        artifact_ref="artifact:love-study:final:001",
        synthesis_ref="synthesis:love-study:001",
        title="Comprendre les dynamiques de l'amour",
        body=(
            "Les deux spécialistes distinguent les dimensions affectives, "
            "conceptuelles et relationnelles sans réduire leur désaccord."
        ),
        evidence_refs=("evidence:concept:1", "evidence:relation:2"),
        context_influence_refs=("context-influence:love:1",),
        validation_refs=("validation:liaison:1",),
    )
    return SimpleNamespace(
        schema="missipy.love.memory_evidence_synthesis_result.v1",
        final_envelope=envelope,
        synthesis=SimpleNamespace(final_publication_ready=ready),
        synthesis_revision=SimpleNamespace(revision_ref="revision:synthesis:001"),
        mutualization=SimpleNamespace(
            convergences=("L'amour est relationnel et affectif.",),
            contradictions=("La stabilité et la transformation restent en tension.",),
            uncertainties=("Le poids du contexte culturel reste incertain.",),
            recommendations=("Conserver les deux angles dans le livrable.",),
            evidence_refs=("evidence:concept:1", "evidence:relation:2"),
        ),
        study_result=SimpleNamespace(
            status="synthesized",
            context_revision_ref="context-revision:love:001",
            unresolved_points=("Mesurer l'effet de la durée.",),
        ),
        github_mutation_performed=github_mutation_performed,
    )


def _command(**changes):
    values = {
        "repository": "newicody/projects",
        "issue_number": 42,
        "source_issue_ref": "github-frame:newicody/projects/issues/42",
        "policy_decision_id": "policy:love-final:001",
        "operator_decision": "approve",
        "synthesis_result": _result(),
        "project_item_id": "PVTI_love42",
        "project_field_ref": "PVTF_status",
        "project_field_name": "Status",
        "project_status_value": "Terminé",
    }
    values.update(changes)
    return LoveFinalDeliverablePublicationCommand(**values)


def test_plan_builds_deterministic_issue_and_project_operations() -> None:
    first = plan_love_final_deliverable_publication(_command())
    second = plan_love_final_deliverable_publication(_command())

    assert first == second
    assert first.valid is True
    assert first.action == "create_and_project"
    assert first.issue_action == "create"
    assert first.project_action == "update"
    assert first.marker.startswith(f"{MARKER_PREFIX}:")
    assert "autodoc:copilot-advisory" not in first.marker
    assert "### Contradictions conservées" in first.body
    assert "### Incertitudes et points non résolus" in first.body
    assert "<details>" in first.body
    assert "evidence:concept:1" in first.body
    assert len(first.plan_digest) == 64
    assert [operation.kind for operation in first.operations] == [
        "create_issue_comment",
        "update_project_v2_field",
    ]
    assert first.operations[1].depends_on == ("create_issue_comment",)
    assert first.github_issue_mutation_allowed is False
    assert first.project_v2_mutation_allowed is False
    assert first.github_mutation_performed is False


def test_exact_existing_surfaces_produce_replay_without_operations() -> None:
    initial = plan_love_final_deliverable_publication(_command())
    assert initial.project_projection is not None
    command = _command(
        existing_comments=(
            GitHubIssueCommentSnapshot(comment_id=7, body=initial.body),
        ),
        project_snapshot=ProjectV2FieldSnapshot(
            project_item_id=initial.project_projection.project_item_id,
            field_ref=initial.project_projection.field_ref,
            field_name=initial.project_projection.field_name,
            value=initial.project_projection.value,
        ),
    )

    replay = plan_love_final_deliverable_publication(command)

    assert replay.valid is True
    assert replay.action == "replay"
    assert replay.issue_action == "replay"
    assert replay.project_action == "replay"
    assert replay.operations == ()
    assert replay.existing_comment_id == 7


def test_changed_marked_comment_fails_closed_as_collision() -> None:
    initial = plan_love_final_deliverable_publication(_command())
    collision = plan_love_final_deliverable_publication(
        _command(
            existing_comments=(
                GitHubIssueCommentSnapshot(
                    comment_id=9,
                    body=f"<!-- {initial.marker} -->\ncontenu altéré",
                ),
            )
        )
    )

    assert collision.valid is False
    assert collision.action == "collision"
    assert collision.issue_action == "collision"
    assert collision.operations == ()
    assert "different body" in collision.issues[0]


def test_mismatched_project_snapshot_identity_blocks_plan() -> None:
    blocked = plan_love_final_deliverable_publication(
        _command(
            project_snapshot=ProjectV2FieldSnapshot(
                project_item_id="PVTI_other",
                field_ref="PVTF_status",
                field_name="Status",
                value="En cours",
            )
        )
    )

    assert blocked.valid is False
    assert blocked.action == "blocked"
    assert blocked.project_action == "blocked"
    assert blocked.operations == ()


def test_plan_digest_covers_policy_and_project_value() -> None:
    baseline = plan_love_final_deliverable_publication(_command())
    changed_policy = plan_love_final_deliverable_publication(
        _command(policy_decision_id="policy:love-final:002")
    )
    changed_value = plan_love_final_deliverable_publication(
        _command(project_status_value="Prod")
    )

    assert baseline.plan_digest != changed_policy.plan_digest
    assert baseline.plan_digest != changed_value.plan_digest


def test_exact_readback_is_confirmed_and_mismatch_is_rejected() -> None:
    plan = plan_love_final_deliverable_publication(_command())
    assert plan.project_projection is not None
    comment = GitHubIssueCommentSnapshot(
        comment_id=12,
        body=plan.body,
        html_url="https://example.invalid/comment/12",
    )
    snapshot = ProjectV2FieldSnapshot(
        project_item_id=plan.project_projection.project_item_id,
        field_ref=plan.project_projection.field_ref,
        field_name=plan.project_projection.field_name,
        value=plan.project_projection.value,
    )

    confirmed = verify_love_final_deliverable_publication_readback(
        plan,
        issue_comments=(comment,),
        project_snapshot=snapshot,
    )
    rejected = verify_love_final_deliverable_publication_readback(
        plan,
        issue_comments=(comment,),
        project_snapshot=ProjectV2FieldSnapshot(
            project_item_id=snapshot.project_item_id,
            field_ref=snapshot.field_ref,
            field_name=snapshot.field_name,
            value="En cours",
        ),
    )

    assert confirmed.valid is True
    assert confirmed.action == "confirmed"
    assert confirmed.plan_digest == plan.plan_digest
    assert rejected.valid is False
    assert rejected.action == "blocked"
    assert "differs" in rejected.issues[0]


@pytest.mark.parametrize(
    "synthesis_result",
    [
        _result(github_mutation_performed=True),
        _result(ready=False),
    ],
)
def test_incomplete_or_already_mutated_r12_result_is_rejected(
    synthesis_result,
) -> None:
    plan = plan_love_final_deliverable_publication(
        _command(synthesis_result=synthesis_result)
    )

    assert plan.valid is False
    assert plan.action == "blocked"
    assert plan.plan_digest == ""
