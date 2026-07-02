from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate import SourceCandidateDecision, SourceCandidateInput, build_source_candidate
from context.source_candidate_decision import (
    SourceCandidateDecisionAuditPolicy,
    SourceCandidateDecisionCommand,
    run_source_candidate_decision,
)
from context.source_candidate_operator_report import (
    SourceCandidateOperatorReportPolicy,
    build_source_candidate_operator_report,
)
from context.source_candidate_operator_report_cli import main
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    run_source_candidate_review,
)
from context.source_candidate_review_audit import (
    SourceCandidateReviewAuditPolicy,
    enrich_source_candidate_review_with_audit,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _review_audit(tmp_path: Path):
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    first = build_source_candidate(
        SourceCandidateInput(title="Operator fresh", body="Needs an operator decision")
    ).candidate
    second = build_source_candidate(
        SourceCandidateInput(title="Operator archived", body="Already handled")
    ).candidate
    upsert_source_candidate(store_policy, first)
    upsert_source_candidate(store_policy, second)
    audit_path = tmp_path / "audit" / "archive.json"
    run_source_candidate_decision(
        SourceCandidateDecisionCommand(
            store_policy=store_policy,
            candidate_id=second.candidate_id,
            decision=SourceCandidateDecision(action="archive", reason="done"),
            audit_policy=SourceCandidateDecisionAuditPolicy(audit_path),
        )
    )
    review = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(include_terminal=True),
        )
    )
    return (
        store_policy,
        audit_path,
        enrich_source_candidate_review_with_audit(
            review,
            SourceCandidateReviewAuditPolicy(audit_paths=(audit_path,)),
        ),
    )


def test_operator_report_builds_counts_and_next_actions(tmp_path: Path) -> None:
    _store_policy, _audit_path, review_audit = _review_audit(tmp_path)
    report = build_source_candidate_operator_report(review_audit)
    payload = report.to_json_dict()

    assert payload["schema"] == "missipy.source_candidate.operator_report.v1"
    assert payload["returned_count"] == 2
    assert payload["audit_present_count"] == 1
    assert payload["status_counts"] == {"archived": 1, "new": 1}
    assert payload["decision_counts"] == {"archive": 1, "none": 1}
    assert payload["actionable_count"] == 1
    assert payload["terminal_count"] == 1
    assert payload["next_actions"][0]["recommended_next_action"] == "inspect"
    assert "SourceCandidate operator report" in report.to_text()


def test_operator_report_can_hide_items(tmp_path: Path) -> None:
    _store_policy, _audit_path, review_audit = _review_audit(tmp_path)
    report = build_source_candidate_operator_report(
        review_audit,
        SourceCandidateOperatorReportPolicy(include_items=False),
    )
    payload = report.to_json_dict()

    assert "items" not in payload
    assert payload["next_actions"]


def test_operator_report_cli_renders_json(tmp_path: Path, capsys) -> None:
    store_policy, audit_path, _review_audit_result = _review_audit(tmp_path)
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
    assert payload["returned_count"] == 2
    assert payload["audit_present_count"] == 1
    assert payload["status_counts"]["archived"] == 1
