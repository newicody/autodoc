from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate import SourceCandidateDecision, SourceCandidateInput, build_source_candidate
from context.source_candidate_decision import (
    SourceCandidateDecisionAuditPolicy,
    SourceCandidateDecisionCommand,
    run_source_candidate_decision,
)
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    run_source_candidate_review,
)
from context.source_candidate_review_audit import (
    SourceCandidateReviewAuditPolicy,
    enrich_source_candidate_review_with_audit,
)
from context.source_candidate_review_audit_cli import main
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _store_with_decided_candidate(tmp_path: Path) -> tuple[SourceCandidateStorePolicy, str, Path]:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Review audit target", body="Review this audit trail")
    ).candidate
    upsert_source_candidate(store_policy, candidate)
    audit_path = tmp_path / "audit" / "decision.json"
    result = run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=candidate.candidate_id,
            decision=SourceCandidateDecision(action="archive", reason="done"),
            audit_policy=SourceCandidateDecisionAuditPolicy(audit_path),
        )
    )
    return store_policy, result.candidate_id, audit_path


def test_review_audit_summary_uses_stored_decision_and_audit_file(tmp_path: Path) -> None:
    store_policy, candidate_id, audit_path = _store_with_decided_candidate(tmp_path)
    review = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(include_terminal=True),
        )
    )

    result = enrich_source_candidate_review_with_audit(
        review,
        SourceCandidateReviewAuditPolicy(audit_paths=(audit_path,)),
    )

    payload = result.to_json_dict()
    assert payload["schema"] == "missipy.source_candidate.review_audit.v1"
    assert result.audit_count == 1
    assert result.items[0].candidate_id == candidate_id
    assert result.items[0].decision is not None
    assert result.items[0].decision.action == "archive"
    assert result.items[0].audit is not None
    assert result.items[0].audit.path == audit_path
    assert payload["items"][0]["audit_present"] is True
    assert payload["items"][0]["decision_summary"]["reason"] == "done"
    assert "audit:" in result.to_text()


def test_review_audit_summary_handles_missing_audit_file(tmp_path: Path) -> None:
    store_policy, _candidate_id, _audit_path = _store_with_decided_candidate(tmp_path)
    review = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(include_terminal=True),
        )
    )

    result = enrich_source_candidate_review_with_audit(
        review,
        SourceCandidateReviewAuditPolicy(audit_paths=(tmp_path / "missing.json",)),
    )

    assert result.audit_count == 0
    assert result.items[0].decision is not None
    assert result.items[0].audit is None
    assert result.items[0].to_json_dict()["audit_present"] is False


def test_review_audit_cli_renders_json_summary(tmp_path: Path, capsys) -> None:
    store_policy, candidate_id, audit_path = _store_with_decided_candidate(tmp_path)

    exit_code = main(
        [
            "--store-file",
            str(store_policy.path),
            "--include-terminal",
            "--audit-file",
            str(audit_path),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["audit_count"] == 1
    assert payload["items"][0]["candidate_id"] == candidate_id
    assert payload["items"][0]["audit_summary"]["path"] == str(audit_path)
