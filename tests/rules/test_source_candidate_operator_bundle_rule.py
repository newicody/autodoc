from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_source_candidate_operator_bundle_is_local_artifact_bundle() -> None:
    source = _read("src/context/source_candidate_operator_bundle.py")
    assert "write_source_candidate_operator_bundle" in source
    assert "manifest.json" in source
    assert "write_source_candidate_operator_report_file" in source
    assert "os.replace" in source


def test_source_candidate_operator_bundle_cli_reuses_operator_report_chain() -> None:
    cli = _read("src/context/source_candidate_operator_bundle_cli.py")
    assert "run_source_candidate_operator_report_via_scheduler" in cli
    assert "Scheduler(" not in cli
    assert "Dispatcher(" not in cli


def test_source_candidate_operator_bundle_adds_no_external_backend_tokens() -> None:
    combined = (
        _read("src/context/source_candidate_operator_bundle.py")
        + _read("src/context/source_candidate_operator_bundle_cli.py")
    ).lower()
    for token in ("requests", "qdrant", "openvino", "subprocess"):
        assert token not in combined


def test_phase6_10_documents_operator_bundle() -> None:
    assert (ROOT / "doc/reports/phase6/PHASE6_10_TEST_REPORT.md").exists()
    assert (ROOT / "doc/changelogs/CHANGELOG_PHASE6_10_SOURCE_CANDIDATE_OPERATOR_BUNDLE.md").exists()
    assert (ROOT / "doc/docs/architecture/context/51_source_candidate_operator_bundle.dot").exists()
