from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_operator_report_is_additive_projection() -> None:
    report = _read("src/context/source_candidate_operator_report.py")
    assert "build_source_candidate_operator_report" in report
    assert "SourceCandidateOperatorReportResult" in report
    assert "load_source_candidate_store" not in report
    assert "upsert_source_candidate" not in report


def test_source_candidate_operator_report_cli_reuses_existing_review_live_path() -> None:
    cli = _read("src/context/source_candidate_operator_report_cli.py")
    assert "run_source_candidate_review_audit_via_scheduler" in cli
    assert "Scheduler(" not in cli
    assert "Dispatcher(" not in cli


def test_source_candidate_operator_report_adds_no_external_backend_tokens() -> None:
    combined = (
        _read("src/context/source_candidate_operator_report.py")
        + _read("src/context/source_candidate_operator_report_cli.py")
    ).lower()
    for token in ("requests", "qdrant", "openvino", "subprocess"):
        assert token not in combined
