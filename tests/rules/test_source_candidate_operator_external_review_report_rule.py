from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_operator_external_review_report_is_local_only() -> None:
    source = _read("src/context/source_candidate_operator_external_review_report.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for token in forbidden:
        assert token not in source


def test_operator_external_review_report_reads_bundle_artifacts() -> None:
    source = _read("src/context/source_candidate_operator_external_review_report.py")
    assert "manifest.json" in source
    assert "remote_mutation_gate" in source
    assert "github_adapter_dry_run" in source


def test_operator_external_review_report_uses_doc_manifest_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_8_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_operator_external_review_report.py" in manifest


def test_operator_external_review_report_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/64_source_candidate_operator_external_review_report.dot"
    svg = ROOT / "doc/docs/architecture/context/64_source_candidate_operator_external_review_report.svg"
    assert dot.exists()
    assert not svg.exists()
