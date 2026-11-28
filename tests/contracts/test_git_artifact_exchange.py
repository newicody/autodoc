from __future__ import annotations

import pytest

from contracts.git_artifact_exchange import (
    GitArtifactExchangeError,
    artifact_path,
    build_git_exchange_artifact,
    classify_existing_path,
    validate_git_exchange_artifact,
    validate_git_exchange_chain,
)


REPOSITORY = "newicody/projects"
CREATED_AT = "2026-11-28T17:00:00Z"


def _chain():
    initial = build_git_exchange_artifact(
        repository=REPOSITORY,
        issue_number=42,
        cycle_ordinal=1,
        role="copilot_initial",
        payload={"objective": "Analyse", "representations": ["table", "curve"]},
        created_at=CREATED_AT,
    )
    initial_map = initial.to_mapping()
    response = build_git_exchange_artifact(
        repository=REPOSITORY,
        issue_number=42,
        cycle_ordinal=1,
        role="server_response",
        payload={"coherence": "partial", "supported": ["table", "curve"]},
        created_at=CREATED_AT,
        predecessor_ref=initial.artifact_ref,
        predecessor_digest=initial.payload_digest,
    )
    response_map = response.to_mapping()
    refined = build_git_exchange_artifact(
        repository=REPOSITORY,
        issue_number=42,
        cycle_ordinal=1,
        role="copilot_refined",
        payload={"objective": "Analyse les données disponibles", "criteria": ["sources"]},
        created_at=CREATED_AT,
        predecessor_ref=response.artifact_ref,
        predecessor_digest=response.payload_digest,
    )
    return initial_map, response_map, refined.to_mapping()


def test_paths_are_deterministic_and_scoped_to_issue_and_cycle():
    assert artifact_path(42, 1, "copilot_initial") == (
        "autodoc/exchanges/issues/42/cycles/1/copilot-initial.json"
    )
    assert artifact_path(42, 2, "server_response") != artifact_path(
        42, 1, "server_response"
    )


def test_valid_git_push_exchange_has_exact_three_artifacts():
    chain = _chain()
    result = validate_git_exchange_chain(chain)
    assert result["valid"] is True
    assert result["transport"] == "git_commit_push"
    assert result["exchange_count"] == 1
    assert result["recursive_clarification_allowed"] is False
    assert result["execution_authorized"] is False


def test_exchange_rejects_broken_predecessor_digest():
    initial, response, refined = _chain()
    response["predecessor_digest"] = "0" * 64
    with pytest.raises(GitArtifactExchangeError, match="does not bind"):
        validate_git_exchange_chain((initial, response, refined))


def test_exchange_rejects_wrong_repository_cycle_or_order():
    initial, response, refined = _chain()
    refined["repository"] = "attacker/other"
    with pytest.raises(GitArtifactExchangeError, match="artifact_ref mismatch|share one"):
        validate_git_exchange_chain((initial, response, refined))
    with pytest.raises(GitArtifactExchangeError, match="order"):
        validate_git_exchange_chain((response, initial, refined))


def test_artifact_payload_digest_is_verified():
    initial, _, _ = _chain()
    initial["payload"]["objective"] = "tampered"
    with pytest.raises(GitArtifactExchangeError, match="payload_digest"):
        validate_git_exchange_artifact(initial)


def test_same_path_is_replay_or_collision_never_overwrite():
    initial, _, _ = _chain()
    assert classify_existing_path(None, initial) == "create"
    assert classify_existing_path(initial, initial) == "replay"
    changed = dict(initial)
    changed["payload"] = {"objective": "different"}
    changed["payload_digest"] = "1" * 64
    with pytest.raises(GitArtifactExchangeError, match="payload_digest"):
        classify_existing_path(initial, changed)


def test_actions_artifacts_and_direct_calls_are_not_the_transport():
    initial, _, _ = _chain()
    assert initial["transport"] == "git_commit_push"
    assert initial["github_actions_artifact_is_transport"] is False
    assert initial["direct_copilot_server_call"] is False


def test_invalid_role_and_issue_path_are_rejected():
    with pytest.raises(GitArtifactExchangeError):
        artifact_path(0, 1, "copilot_initial")
    with pytest.raises(GitArtifactExchangeError):
        artifact_path(42, 1, "../server-response")
