from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_remote_mutation_gate import (
    SourceCandidateRemoteMutationGatePolicy,
    render_source_candidate_remote_mutation_gate,
    run_source_candidate_remote_mutation_gate,
    run_source_candidate_remote_mutation_gate_from_file,
    write_source_candidate_remote_mutation_gate_result,
)


def _payload(*, allowed: bool = True, safety_flags: list[str] | None = None) -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.github_projection_payload.v1",
        "repository": "newicody/autodoc",
        "project_key": None,
        "dry_run": True,
        "remote_mutation": False,
        "projection_allowed": allowed,
        "blocked_reasons": [] if allowed else ["gate_not_passed"],
        "operation_count": 1,
        "operations": [
            {
                "action": "create_issue",
                "candidate_id": "candidate-a",
                "title": "SourceCandidate: Ready",
                "body": "dry-run body",
                "labels": ["autodoc", "source-candidate", "dry-run"],
                "safety_flags": safety_flags or [],
            }
        ],
    }


def _open_policy() -> SourceCandidateRemoteMutationGatePolicy:
    return SourceCandidateRemoteMutationGatePolicy(
        remote_mutation_enabled=True,
        operator_confirmed=True,
        allowed_repositories=("newicody/autodoc",),
    )


def test_remote_mutation_gate_is_closed_by_default() -> None:
    result = run_source_candidate_remote_mutation_gate(_payload())

    assert result.mutation_allowed is False
    assert any(issue.code == "remote_mutation_disabled" for issue in result.issues)
    assert any(issue.code == "operator_not_confirmed" for issue in result.issues)
    assert any(issue.code == "repository_allowlist_missing" for issue in result.issues)


def test_remote_mutation_gate_can_pass_with_explicit_policy() -> None:
    result = run_source_candidate_remote_mutation_gate(_payload(), _open_policy())

    assert result.mutation_allowed is True
    assert result.issue_count == 0
    assert result.operation_count == 1


def test_remote_mutation_gate_blocks_repository_not_in_allowlist() -> None:
    result = run_source_candidate_remote_mutation_gate(
        _payload(),
        SourceCandidateRemoteMutationGatePolicy(
            remote_mutation_enabled=True,
            operator_confirmed=True,
            allowed_repositories=("other/repo",),
        ),
    )

    assert result.mutation_allowed is False
    assert any(issue.code == "repository_not_allowed" for issue in result.issues)


def test_remote_mutation_gate_blocks_projection_denied() -> None:
    result = run_source_candidate_remote_mutation_gate(_payload(allowed=False), _open_policy())

    assert result.mutation_allowed is False
    assert any(issue.code == "projection_blocked" for issue in result.issues)


def test_remote_mutation_gate_can_require_no_safety_flags() -> None:
    result = run_source_candidate_remote_mutation_gate(
        _payload(safety_flags=["audit_missing"]),
        SourceCandidateRemoteMutationGatePolicy(
            remote_mutation_enabled=True,
            operator_confirmed=True,
            allowed_repositories=("newicody/autodoc",),
            require_no_safety_flags=True,
        ),
    )

    assert result.mutation_allowed is False
    assert any(issue.code == "safety_flags_present" for issue in result.issues)


def test_remote_mutation_gate_writes_result(tmp_path: Path) -> None:
    output = tmp_path / "remote_mutation_gate.json"
    result = run_source_candidate_remote_mutation_gate(_payload(), _open_policy())

    returned = write_source_candidate_remote_mutation_gate_result(output, result)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.remote_mutation_gate.v1"
    assert payload["mutation_allowed"] is True


def test_remote_mutation_gate_reads_payload_from_file(tmp_path: Path) -> None:
    payload_path = tmp_path / "github_projection_payload.json"
    payload_path.write_text(json.dumps(_payload()) + "\n", encoding="utf-8")

    result = run_source_candidate_remote_mutation_gate_from_file(payload_path, _open_policy())

    assert result.mutation_allowed is True


def test_remote_mutation_gate_render_is_stable() -> None:
    rendered = render_source_candidate_remote_mutation_gate(
        run_source_candidate_remote_mutation_gate(_payload())
    )

    assert "remote mutation gate: FAIL" in rendered
    assert "repository: newicody/autodoc" in rendered
