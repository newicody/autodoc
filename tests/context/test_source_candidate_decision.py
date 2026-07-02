from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate import SourceCandidateDecision, SourceCandidateInput, build_source_candidate
from context.source_candidate_decision import (
    SourceCandidateDecisionCommand,
    run_source_candidate_decision,
)
from context.source_candidate_store import (
    SourceCandidateReportPolicy,
    SourceCandidateStorePolicy,
    load_source_candidate_store,
    upsert_source_candidate,
)


def _store_with_candidate(tmp_path: Path) -> tuple[SourceCandidateStorePolicy, str]:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Decision target", body="Review this candidate")
    ).candidate
    upsert_source_candidate(policy, candidate)
    return policy, candidate.candidate_id


def test_source_candidate_decision_updates_existing_candidate(tmp_path: Path) -> None:
    store_policy, candidate_id = _store_with_candidate(tmp_path)

    result = run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=candidate_id,
            decision=SourceCandidateDecision(action="reject", reason="not useful"),
        )
    )

    assert result.candidate_id == candidate_id
    assert result.before_status == "new"
    assert result.after_status == "rejected"
    assert result.action == "reject"
    assert result.write_result.replaced is True

    reloaded = load_source_candidate_store(store_policy).find(candidate_id)
    assert reloaded is not None
    assert reloaded.status == "rejected"
    assert reloaded.decision is not None
    assert reloaded.decision.reason == "not useful"


def test_source_candidate_decision_writes_optional_report(tmp_path: Path) -> None:
    store_policy, candidate_id = _store_with_candidate(tmp_path)
    report_path = tmp_path / "decision_report.json"

    run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=candidate_id,
            decision=SourceCandidateDecision(action="promote", reason="good source"),
            report_policy=SourceCandidateReportPolicy(report_path),
        )
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.source_candidate.store_report.v1"
    assert payload["write_result"]["candidate_id"] == candidate_id


def test_source_candidate_decision_rejects_unknown_candidate(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown SourceCandidate"):
        run_source_candidate_decision(
            SourceCandidateDecisionCommand(
                store_policy=SourceCandidateStorePolicy(tmp_path / "missing.json"),
                candidate_id="sc-missing",
                decision=SourceCandidateDecision(action="archive"),
            )
        )
