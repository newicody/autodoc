from __future__ import annotations

import pytest

from context.source_candidate import (
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    SourceCandidatePolicy,
    allowed_source_candidate_decisions,
    allowed_source_candidate_statuses,
    apply_source_candidate_decision,
    build_source_candidate,
)


def test_source_candidate_builds_deterministic_local_contract() -> None:
    candidate_input = SourceCandidateInput(
        title="OpenVINO local context loop",
        body="Artifact-dir ready for local context intake.",
        origin=SourceCandidateOrigin(kind="artifact_dir", reference="/tmp/autodoc_e5_dry_run"),
        labels=("e5", "context"),
        metadata={"phase": "5.14", "selected_item_count": 5},
    )

    first = build_source_candidate(candidate_input)
    second = build_source_candidate(candidate_input)

    assert first.candidate.candidate_id == second.candidate.candidate_id
    assert first.candidate.candidate_id.startswith("sc-")
    assert first.candidate.status == "new"
    assert first.candidate.origin.repository == "newicody/autodoc"
    payload = first.to_json_dict()
    assert payload["schema"] == "missipy.source_candidate.creation.v1"
    assert payload["candidate"]["schema"] == "missipy.source_candidate.v1"
    assert payload["candidate"]["origin"]["kind"] == "artifact_dir"
    assert payload["candidate"]["origin"]["repository"] == "newicody/autodoc"
    assert payload["candidate"]["labels"] == ["e5", "context"]
    assert payload["candidate"]["metadata"]["selected_item_count"] == 5
    assert payload["candidate"]["terminal"] is False
    assert payload["candidate"]["actionable"] is True


def test_source_candidate_policy_can_disable_default_repository() -> None:
    candidate_input = SourceCandidateInput(
        title="Manual note",
        body="Local-only candidate.",
        origin=SourceCandidateOrigin(kind="manual", reference="operator-note"),
    )

    result = build_source_candidate(candidate_input, SourceCandidatePolicy(default_repository=None))

    assert result.candidate.origin.repository is None


def test_source_candidate_decision_returns_new_terminal_candidate() -> None:
    candidate = build_source_candidate(
        SourceCandidateInput(title="Candidate", body="Needs archive."),
    ).candidate
    decided = apply_source_candidate_decision(
        candidate,
        SourceCandidateDecision(action="archive", reason="not useful for current context"),
    )

    assert candidate.status == "new"
    assert candidate.decision is None
    assert decided.status == "archived"
    assert decided.terminal is True
    assert decided.actionable is False
    assert decided.decision is not None
    assert decided.decision.action == "archive"
    assert decided.to_json_dict()["decision"]["resulting_status"] == "archived"


def test_source_candidate_merge_decision_can_target_existing_context() -> None:
    candidate = build_source_candidate(SourceCandidateInput(title="Merge me", body="payload")).candidate

    decided = candidate.with_decision(SourceCandidateDecision(action="merge", target_context_id="ctx-e5-local"))

    assert decided.status == "merged"
    assert decided.decision is not None
    assert decided.decision.target_context_id == "ctx-e5-local"


def test_source_candidate_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="title must not be empty"):
        SourceCandidateInput(title=" ", body="payload")

    with pytest.raises(ValueError, match="origin kind"):
        SourceCandidateOrigin(kind="network")

    with pytest.raises(ValueError, match="action must be"):
        SourceCandidateDecision(action="delete")

    with pytest.raises(ValueError, match="labels must"):
        SourceCandidateInput(title="Bad label", body="payload", labels=("",))


def test_allowed_source_candidate_values_are_stable() -> None:
    assert allowed_source_candidate_decisions() == ("archive", "inspect", "merge", "promote", "reject", "relaunch")
    assert allowed_source_candidate_statuses() == ("analyzed", "archived", "merged", "new", "promoted", "rejected")
