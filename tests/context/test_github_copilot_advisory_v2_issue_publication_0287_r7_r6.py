from __future__ import annotations

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.github_copilot_advisory_v2_issue_publication_0287 import (
    CopilotAdvisoryV2IssuePublicationCommand,
    plan_copilot_advisory_v2_issue_publication,
)


def _preview() -> dict[str, object]:
    return {
        "schema": "missipy.github.copilot_advisory_publication_preview.v2",
        "source_candidate_ref": "github-request:42",
        "advisory_artifact_ref": "github-copilot-advisory:42",
        "concrete_objective": "Identifier le besoin concret.",
        "expected_result": "Une étude exploitable.",
        "provided_constraints": ["Conserver la demande comme autorité."],
        "success_criteria": ["Le résultat est observable."],
        "workflow_run_ref": "github-actions-run:99",
        "response_digest": "a" * 64,
        "repository": "newicody/projects",
        "issue_number": 42,
        "advisory_schema": "missipy.github.copilot_advisory.v2",
        "request_authoritative": True,
        "advisory_is_authority": False,
        "operator_decision_required": True,
        "publication_gate_required": True,
        "github_mutation_performed": False,
        "remote_mutation_allowed": False,
    }


def _command(comments: tuple[GitHubIssueCommentSnapshot, ...] = ()):
    return CopilotAdvisoryV2IssuePublicationCommand(
        repository="newicody/projects",
        issue_number=42,
        policy_decision_id="policy:copilot-v2-publish",
        operator_decision="approve",
        publication_preview=_preview(),
        existing_comments=comments,
    )


def test_create_replay_and_collision_are_deterministic() -> None:
    create = plan_copilot_advisory_v2_issue_publication(_command())
    assert create.valid is True
    assert create.action == "create"
    assert "Objectif concret" in create.body
    assert "Critères de réussite observables" in create.body
    assert "consultatif et non autoritatif" in create.body

    existing = GitHubIssueCommentSnapshot(1, create.body, "https://example/1")
    replay = plan_copilot_advisory_v2_issue_publication(_command((existing,)))
    assert replay.action == "replay"
    assert replay.plan_digest == create.plan_digest

    changed = GitHubIssueCommentSnapshot(1, create.body + "changed", "")
    collision = plan_copilot_advisory_v2_issue_publication(_command((changed,)))
    assert collision.valid is False
    assert collision.action == "collision"


def test_invalid_authority_or_empty_criteria_fails_closed() -> None:
    preview = _preview()
    preview["advisory_is_authority"] = True
    preview["success_criteria"] = []
    command = CopilotAdvisoryV2IssuePublicationCommand(
        repository="newicody/projects",
        issue_number=42,
        policy_decision_id="policy:copilot-v2-publish",
        operator_decision="approve",
        publication_preview=preview,
    )
    plan = plan_copilot_advisory_v2_issue_publication(command)
    assert plan.valid is False
    assert "advisory_is_authority must remain false" in plan.issues
    assert "success_criteria must not be empty" in plan.issues
