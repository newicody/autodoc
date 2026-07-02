from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_operator_summary_is_local_only() -> None:
    source = _read("src/context/source_candidate_external_probe_operator_summary.py").lower()
    cli = _read("tools/source_candidate_external_probe_operator_summary_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source
        assert forbidden_text not in cli


def test_external_probe_operator_summary_uses_index_schema() -> None:
    source = _read("src/context/source_candidate_external_probe_operator_summary.py")
    assert "missipy.source_candidate.external_probe_artifact_index.v1" in source
    assert "ready_count" in source
    assert "blocked_count" in source


def test_external_probe_operator_summary_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_16_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_external_probe_operator_summary.py" in manifest


def test_external_probe_operator_summary_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_16_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
