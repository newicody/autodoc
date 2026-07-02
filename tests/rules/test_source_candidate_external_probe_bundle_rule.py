from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_bundle_is_local_only() -> None:
    source = _read("src/context/source_candidate_external_probe_bundle.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source


def test_external_probe_bundle_preserves_read_only_result() -> None:
    source = _read("src/context/source_candidate_external_probe_bundle.py")
    assert "external_call_performed" in source
    assert "read_only" in source
    assert "probe_allowed" in source


def test_external_probe_bundle_uses_post_migration_manifest_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_11_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_external_probe_bundle.py" in manifest


def test_external_probe_bundle_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/66_source_candidate_external_probe_bundle.dot"
    svg = ROOT / "doc/docs/architecture/context/66_source_candidate_external_probe_bundle.svg"
    assert dot.exists()
    assert not svg.exists()
