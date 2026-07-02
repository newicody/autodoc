from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_review_audit_is_local_projection_only() -> None:
    source = _read("src/context/source_candidate_review_audit.py").lower()
    for token in ("requests", "qdrant", "openvino", "subprocess"):
        assert token not in source


def test_source_candidate_review_audit_cli_reuses_review_scheduler_path() -> None:
    cli = _read("src/context/source_candidate_review_audit_cli.py")
    assert "run_source_candidate_review_via_scheduler" in cli
    assert "Scheduler(" not in cli


def test_phase6_7_documents_review_audit_summary() -> None:
    assert (ROOT / "PHASE6_7_TEST_REPORT.md").exists()
    assert (ROOT / "doc/CHANGELOG_PHASE6_7_SOURCE_CANDIDATE_REVIEW_AUDIT.md").exists()
    assert (ROOT / "doc/docs/architecture/context/48_source_candidate_review_audit_summary.dot").exists()
