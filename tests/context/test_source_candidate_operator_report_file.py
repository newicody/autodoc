from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate import SourceCandidateInput, build_source_candidate
from context.source_candidate_operator_report import build_source_candidate_operator_report
from context.source_candidate_operator_report_file import (
    SourceCandidateOperatorReportFilePolicy,
    write_source_candidate_operator_report_file,
)
from context.source_candidate_operator_report_file_cli import main
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


def _store(tmp_path: Path) -> SourceCandidateStorePolicy:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(title="Report file candidate", body="Needs reporting")
    ).candidate
    upsert_source_candidate(store_policy, candidate)
    return store_policy


def _report(tmp_path: Path):
    store_policy = _store(tmp_path)
    review = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(),
        )
    )
    review_audit = enrich_source_candidate_review_with_audit(
        review,
        SourceCandidateReviewAuditPolicy(),
    )
    return store_policy, build_source_candidate_operator_report(review_audit)


def test_operator_report_file_writes_json_atomically(tmp_path: Path) -> None:
    _store_policy, report = _report(tmp_path)
    output = tmp_path / "reports" / "operator.json"

    result = write_source_candidate_operator_report_file(
        report,
        SourceCandidateOperatorReportFilePolicy(output),
    )

    assert result.path == output
    assert result.output_format == "json"
    assert result.byte_count == len(output.read_bytes())
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.source_candidate.operator_report.v1"
    assert payload["returned_count"] == 1
    assert result.to_json_dict()["schema"] == "missipy.source_candidate.operator_report_file.v1"


def test_operator_report_file_writes_text(tmp_path: Path) -> None:
    _store_policy, report = _report(tmp_path)
    output = tmp_path / "operator.txt"

    result = write_source_candidate_operator_report_file(
        report,
        SourceCandidateOperatorReportFilePolicy(output, output_format="text"),
    )

    assert result.output_format == "text"
    assert "SourceCandidate operator report" in output.read_text(encoding="utf-8")


def test_operator_report_file_cli_writes_artifact_and_renders_summary(tmp_path: Path, capsys) -> None:
    store_policy = _store(tmp_path)
    output = tmp_path / "operator.json"

    exit_code = main(
        [
            "--store-file",
            str(store_policy.path),
            "--output-file",
            str(output),
            "--format",
            "json",
        ]
    )

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["path"] == str(output)
    assert summary["output_format"] == "json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["returned_count"] == 1
