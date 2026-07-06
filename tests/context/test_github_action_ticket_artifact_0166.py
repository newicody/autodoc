from __future__ import annotations

import pytest

from context.github_action_ticket_artifact import (
    GitHubActionProducer,
    build_copilot_preliminary_opinion_for_ticket_artifact,
    build_github_action_ticket_artifact,
    build_github_action_ticket_artifact_bundle,
    validate_github_action_ticket_artifact_bundle,
)
from context.github_project_push_frame import ProjectPushContextOptions


def test_0166_ticket_artifact_contains_ticket_column_and_options_only() -> None:
    artifact = build_github_action_ticket_artifact(
        repository="newicody/autodoc-ideas",
        project_url="https://github.com/users/newicody/projects/2",
        ticket_kind="issue",
        ticket_number=42,
        ticket_title="New task",
        ticket_body="body",
        ticket_url="https://github.com/newicody/autodoc-ideas/issues/42",
        column_name="Backlog",
        context_options=ProjectPushContextOptions(include_total_project=True, include_repository_context=True),
        producer=GitHubActionProducer(repository="newicody/autodoc-ideas", workflow_name="autodoc-ticket-artifact.yml"),
        revision_token="abc",
    )
    payload = artifact.to_json_dict()
    assert payload["schema"] == "missipy.github_action.ticket_artifact.v1"
    assert payload["origin_frame_id"] == "github-frame:newicody/autodoc-ideas/issues/42"
    assert payload["workflow"]["column_name"] == "Backlog"
    assert payload["context_options"]["include_total_project"] is True
    assert payload["context_options"]["include_repository_context"] is True
    assert payload["safety"]["remote_mutation_requested"] is False


def test_0166_bundle_accepts_copilot_as_hint_only() -> None:
    ticket = build_github_action_ticket_artifact(
        repository="newicody/autodoc-ideas",
        project_url="https://github.com/users/newicody/projects/2",
        ticket_kind="issue",
        ticket_number=42,
        ticket_title="New task",
        ticket_body="body",
        ticket_url="https://github.com/newicody/autodoc-ideas/issues/42",
        column_name="Ready",
        revision_token="abc",
    )
    copilot = build_copilot_preliminary_opinion_for_ticket_artifact(ticket, summary="first orientation", suggested_route="architecture_review", risks=("requires local validation",))
    bundle = build_github_action_ticket_artifact_bundle(ticket, copilot)
    payload = bundle.to_json_dict()
    validation = validate_github_action_ticket_artifact_bundle(bundle)
    assert validation["allowed"] is True
    assert payload["server_use_policy"]["copilot_usable_as_hint_only"] is True
    assert payload["artifacts"]["copilot_preliminary_opinion"]["server_use_policy"]["usable_as_authority"] is False


def test_0166_bundle_rejects_copilot_from_other_revision() -> None:
    ticket = build_github_action_ticket_artifact(
        repository="newicody/autodoc-ideas",
        project_url="https://github.com/users/newicody/projects/2",
        ticket_kind="issue",
        ticket_number=42,
        ticket_title="New task",
        ticket_body="body",
        ticket_url="https://github.com/newicody/autodoc-ideas/issues/42",
        column_name="Ready",
        revision_token="abc",
    )
    other = build_github_action_ticket_artifact(
        repository="newicody/autodoc-ideas",
        project_url="https://github.com/users/newicody/projects/2",
        ticket_kind="issue",
        ticket_number=42,
        ticket_title="New task",
        ticket_body="body changed",
        ticket_url="https://github.com/newicody/autodoc-ideas/issues/42",
        column_name="Review",
        revision_token="def",
    )
    copilot = build_copilot_preliminary_opinion_for_ticket_artifact(other, summary="other", suggested_route="architecture_review")
    with pytest.raises(ValueError, match="ticket_revision_id"):
        build_github_action_ticket_artifact_bundle(ticket, copilot)
