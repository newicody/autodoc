from __future__ import annotations

from context.source_candidate_github_adapter import (
    FakeSourceCandidateGithubProjectionAdapter,
    SourceCandidateGithubProjectionAdapter,
)
from context.source_candidate_remote_mutation_gate import SourceCandidateRemoteMutationGatePolicy


def _payload() -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.github_projection_payload.v1",
        "repository": "newicody/autodoc",
        "project_key": None,
        "dry_run": True,
        "remote_mutation": False,
        "projection_allowed": True,
        "blocked_reasons": [],
        "operation_count": 1,
        "operations": [
            {
                "action": "create_issue",
                "candidate_id": "candidate-a",
                "title": "SourceCandidate: Ready",
                "body": "dry-run body",
                "labels": ["autodoc", "source-candidate", "dry-run"],
                "safety_flags": [],
            }
        ],
    }


def _open_policy() -> SourceCandidateRemoteMutationGatePolicy:
    return SourceCandidateRemoteMutationGatePolicy(
        remote_mutation_enabled=True,
        operator_confirmed=True,
        allowed_repositories=("newicody/autodoc",),
    )


def test_fake_github_adapter_satisfies_protocol_shape() -> None:
    adapter: SourceCandidateGithubProjectionAdapter = FakeSourceCandidateGithubProjectionAdapter()

    plan = adapter.plan(_payload())

    assert plan.repository == "newicody/autodoc"
    assert plan.operation_count == 1
    assert plan.operations[0].action == "create_issue"


def test_fake_github_adapter_dry_run_includes_remote_gate() -> None:
    adapter = FakeSourceCandidateGithubProjectionAdapter()

    dry_run = adapter.dry_run(_payload(), SourceCandidateRemoteMutationGatePolicy())

    assert dry_run.plan.operation_count == 1
    assert dry_run.gate.mutation_allowed is False
    assert any(issue.code == "remote_mutation_disabled" for issue in dry_run.gate.issues)


def test_fake_github_adapter_apply_is_blocked_when_gate_fails() -> None:
    adapter = FakeSourceCandidateGithubProjectionAdapter()

    result = adapter.apply(_payload(), SourceCandidateRemoteMutationGatePolicy())

    assert result.applied is False
    assert result.fake_only is True
    assert "remote_mutation_disabled" in result.blocked_reasons
    assert adapter.applied_payloads == []


def test_fake_github_adapter_apply_records_local_simulation_when_gate_passes() -> None:
    adapter = FakeSourceCandidateGithubProjectionAdapter()

    result = adapter.apply(_payload(), _open_policy())

    assert result.applied is True
    assert result.fake_only is True
    assert result.operation_count == 1
    assert len(adapter.applied_payloads) == 1
    assert adapter.applied_payloads[0]["schema"] == "missipy.source_candidate.github_adapter_plan.v1"


def test_fake_github_adapter_serialization_is_stable() -> None:
    adapter = FakeSourceCandidateGithubProjectionAdapter()
    dry_run = adapter.dry_run(_payload(), _open_policy())

    payload = dry_run.to_json_dict()

    assert payload["schema"] == "missipy.source_candidate.github_adapter_dry_run.v1"
    assert payload["plan"]["remote_mutation"] is False
    assert payload["gate"]["mutation_allowed"] is True
