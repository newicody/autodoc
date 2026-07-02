from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_bundle_cli_is_local_only() -> None:
    source = _read("tools/source_candidate_external_probe_bundle_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source


def test_external_probe_bundle_cli_is_dry_run_by_default() -> None:
    source = _read("tools/source_candidate_external_probe_bundle_cli.py")
    assert "apply: bool = False" in source
    assert "writes_bundle" in source


def test_external_probe_bundle_cli_uses_existing_bundle_module() -> None:
    source = _read("tools/source_candidate_external_probe_bundle_cli.py")
    assert "build_source_candidate_external_probe_bundle" in source
    assert "render_source_candidate_external_probe_bundle" in source


def test_external_probe_bundle_cli_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_12_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "tools/source_candidate_external_probe_bundle_cli.py" in manifest
