from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_local_audit_trail_is_local_only() -> None:
    source = _read("src/context/source_candidate_external_probe_local_audit_trail.py").lower()
    cli = _read("tools/source_candidate_external_probe_local_audit_trail_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source
        assert forbidden_text not in cli


def test_external_probe_local_audit_trail_uses_jsonl() -> None:
    source = _read("src/context/source_candidate_external_probe_local_audit_trail.py")
    cli = _read("tools/source_candidate_external_probe_local_audit_trail_cli.py")
    assert ".jsonl" in cli
    assert 'open("a"' in source or ".open(\"a\"" in source


def test_external_probe_local_audit_trail_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_17_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_external_probe_local_audit_trail.py" in manifest


def test_external_probe_local_audit_trail_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_17_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
