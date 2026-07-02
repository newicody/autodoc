from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "doc/runbooks/SOURCE_CANDIDATE_EXTERNAL_PROBE_BUNDLE_RUNBOOK.md"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_bundle_runbook_is_local_only() -> None:
    text = RUNBOOK.read_text(encoding="utf-8").lower()
    forbidden = ("curl ", "wget ", "requests", "httpx", "authorization", "personal access token")
    for forbidden_text in forbidden:
        assert forbidden_text not in text


def test_external_probe_bundle_runbook_keeps_apply_explicit() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")
    assert "Use the CLI without `--apply` first" in text
    assert "Only after the dry-run plan is correct" in text
    assert " --apply" in text


def test_external_probe_bundle_runbook_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_14_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "doc/runbooks/SOURCE_CANDIDATE_EXTERNAL_PROBE_BUNDLE_RUNBOOK.md" in manifest


def test_external_probe_bundle_runbook_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_14_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
