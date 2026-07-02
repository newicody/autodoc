from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_operator_report_file_is_local_artifact_writer() -> None:
    source = _read("src/context/source_candidate_operator_report_file.py")
    assert "write_source_candidate_operator_report_file" in source
    assert "os.replace" in source
    assert "SourceCandidateOperatorReportResult" in source


def test_source_candidate_operator_report_file_cli_reuses_operator_report_live_chain() -> None:
    cli = _read("src/context/source_candidate_operator_report_file_cli.py")
    assert "run_source_candidate_operator_report_via_scheduler" in cli
    assert "Scheduler(" not in cli
    assert "Dispatcher(" not in cli


def test_source_candidate_operator_report_file_adds_no_external_backend_tokens() -> None:
    combined = (
        _read("src/context/source_candidate_operator_report_file.py")
        + _read("src/context/source_candidate_operator_report_file_cli.py")
    ).lower()
    for token in ("requests", "qdrant", "openvino", "subprocess"):
        assert token not in combined


def test_phase6_9_documents_operator_report_file_artifact() -> None:
    assert (ROOT / "doc/reports/phase6/PHASE6_9_TEST_REPORT.md").exists()
    assert (ROOT / "doc/changelogs/CHANGELOG_PHASE6_9_SOURCE_CANDIDATE_OPERATOR_REPORT_FILE.md").exists()
    assert (ROOT / "doc/docs/architecture/context/50_source_candidate_operator_report_file.dot").exists()
