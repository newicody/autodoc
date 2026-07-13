from __future__ import annotations

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubControlledAdvisoryIssuePublicationCommand,
    GitHubIssueCommentSnapshot,
    plan_github_controlled_advisory_issue_publication,
)
from context.github_operator_laboratory_advisory_projection_0281 import (
    PUBLICATION_PREVIEW_SCHEMA,
)


def _preview() -> dict[str, object]:
    return {
        "schema": PUBLICATION_PREVIEW_SCHEMA,
        "source_candidate_ref": "github-request-0123456789abcdef",
        "advisory_context_ref": "ctx:github-advisory:0123456789abcdef01234567",
        "advisory_artifact_ref": "github-advisory:abc",
        "summary": "Comparer les contraintes avant validation.",
        "suggested_route": "Audit, synthèse, validation opérateur.",
        "questions": ["Quelle preuve est requise ?"],
        "risks": ["Contexte incomplet."],
        "confidence": 0.72,
        "laboratory_source_sql_ref": "sql:lab:1",
        "laboratory_source_final_ref": "artifact-final:lab:1",
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "remote_mutation_allowed": False,
        "github_mutation_performed": False,
    }


def _command(comments=()):
    return GitHubControlledAdvisoryIssuePublicationCommand(
        repository="newicody/projects",
        issue_number=15,
        policy_decision_id="policy:0281:r6:test",
        operator_decision="approve",
        publication_preview=_preview(),
        existing_comments=tuple(comments),
    )


def test_new_publication_is_create_and_bounded() -> None:
    plan = plan_github_controlled_advisory_issue_publication(_command())

    assert plan.valid is True
    assert plan.action == "create"
    assert plan.marker.startswith("autodoc:copilot-advisory:")
    assert f"<!-- {plan.marker} -->" in plan.body
    assert "Avis consultatif et non autoritatif" in plan.body
    assert "Comparer les contraintes" in plan.body
    assert plan.github_mutation_allowed is False
    assert plan.github_mutation_performed is False
    assert len(plan.body) <= 12_000


def test_identical_marked_comment_is_idempotent_replay() -> None:
    first = plan_github_controlled_advisory_issue_publication(_command())
    existing = GitHubIssueCommentSnapshot(
        comment_id=42,
        body=first.body,
        html_url="https://github.com/newicody/projects/issues/15#issuecomment-42",
    )

    replay = plan_github_controlled_advisory_issue_publication(
        _command((existing,))
    )

    assert replay.valid is True
    assert replay.action == "replay"
    assert replay.existing_comment_id == 42
    assert replay.body_sha256 == first.body_sha256


def test_changed_marked_comment_is_collision() -> None:
    first = plan_github_controlled_advisory_issue_publication(_command())
    existing = GitHubIssueCommentSnapshot(
        comment_id=42,
        body=first.body + "\nchanged remotely",
    )

    collision = plan_github_controlled_advisory_issue_publication(
        _command((existing,))
    )

    assert collision.valid is False
    assert collision.action == "collision"
    assert "differs" in collision.issues[0]


def test_invalid_authority_flags_block_publication() -> None:
    preview = _preview()
    preview["advisory_is_authority"] = True
    command = GitHubControlledAdvisoryIssuePublicationCommand(
        repository="newicody/projects",
        issue_number=15,
        policy_decision_id="policy:0281:r6:test",
        operator_decision="approve",
        publication_preview=preview,
    )

    plan = plan_github_controlled_advisory_issue_publication(command)

    assert plan.valid is False
    assert plan.action == "blocked"
    assert "advisory_is_authority" in plan.issues[0]
