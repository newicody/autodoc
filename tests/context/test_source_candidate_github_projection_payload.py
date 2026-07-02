from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_github_projection_payload import (
    SourceCandidateGithubProjectionPayloadPolicy,
    build_source_candidate_github_projection_payload,
    build_source_candidate_github_projection_payload_from_file,
    read_source_candidate_github_projection_payload,
    write_source_candidate_github_projection_payload,
)


def _contract(*, allowed: bool = True, safety_flags: list[str] | None = None) -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.external_projection_contract.v1",
        "target_kind": "github_project_surface",
        "source_handoff_path": "/tmp/handoff",
        "gate_passed": allowed,
        "projection_allowed": allowed,
        "blocked_reasons": [] if allowed else ["gate_not_passed"],
        "item_count": 1,
        "items": [
            {
                "candidate_id": "candidate-a",
                "title": "Ready",
                "status": "new",
                "recommended_action": "inspect",
                "audit_present": safety_flags is None,
                "labels": ["status:new", "decision:inspect"],
                "decision_action": "inspect",
                "target_context_id": None,
                "safety_flags": safety_flags or [],
            }
        ],
    }


def test_github_projection_payload_builds_dry_run_operations() -> None:
    payload = build_source_candidate_github_projection_payload(
        _contract(),
        SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
    )

    assert payload.dry_run is True
    assert payload.remote_mutation is False
    assert payload.projection_allowed is True
    assert payload.operation_count == 1
    assert payload.operations[0].action == "create_issue"
    assert "dry-run" in payload.operations[0].labels
    assert "No remote mutation" in payload.operations[0].body


def test_github_projection_payload_blocks_when_contract_is_blocked() -> None:
    payload = build_source_candidate_github_projection_payload(
        _contract(allowed=False),
        SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
    )

    assert payload.projection_allowed is False
    assert payload.blocked_reasons == ("gate_not_passed",)
    assert payload.operation_count == 0


def test_github_projection_payload_preserves_safety_flags_as_labels() -> None:
    payload = build_source_candidate_github_projection_payload(
        _contract(safety_flags=["audit_missing"]),
        SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
    )

    assert payload.operation_count == 1
    assert "safety/audit-missing" in payload.operations[0].labels


def test_github_projection_payload_skips_terminal_items() -> None:
    payload = build_source_candidate_github_projection_payload(
        _contract(safety_flags=["terminal"]),
        SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
    )

    assert payload.operation_count == 0


def test_github_projection_payload_writes_and_reads_json(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    payload_path = tmp_path / "github_projection_payload.json"
    contract_path.write_text(json.dumps(_contract()) + "\n", encoding="utf-8")

    payload = build_source_candidate_github_projection_payload_from_file(
        contract_path,
        SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
    )
    returned = write_source_candidate_github_projection_payload(payload_path, payload)
    reloaded = read_source_candidate_github_projection_payload(payload_path)

    assert returned == payload_path
    assert reloaded["schema"] == "missipy.source_candidate.github_projection_payload.v1"
    assert reloaded["remote_mutation"] is False


def test_github_projection_payload_rejects_invalid_repository() -> None:
    with pytest.raises(ValueError, match="owner/name"):
        build_source_candidate_github_projection_payload(
            _contract(),
            SourceCandidateGithubProjectionPayloadPolicy(repository="autodoc"),
        )


def test_github_projection_payload_rejects_invalid_contract_schema() -> None:
    contract = _contract()
    contract["schema"] = "wrong"

    with pytest.raises(ValueError, match="schema"):
        build_source_candidate_github_projection_payload(
            contract,
            SourceCandidateGithubProjectionPayloadPolicy(repository="newicody/autodoc"),
        )
