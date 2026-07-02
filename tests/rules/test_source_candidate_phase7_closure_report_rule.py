from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase7_closure_report_is_local_only() -> None:
    source = _read("src/context/source_candidate_phase7_closure_report.py").lower()
    cli = _read("tools/source_candidate_phase7_closure_report_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source
        assert forbidden_text not in cli


def test_phase7_closure_report_freezes_remote_boundaries() -> None:
    source = _read("src/context/source_candidate_phase7_closure_report.py")
    assert "remote_mutation_enabled=False" in source
    assert "scheduler_modified=False" in source
    assert "network_enabled=False" in source
    assert "local_only=True" in source


def test_phase7_closure_report_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_19_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_phase7_closure_report.py" in manifest


def test_phase7_closure_report_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_19_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
