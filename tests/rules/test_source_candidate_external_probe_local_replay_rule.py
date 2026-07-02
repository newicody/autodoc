from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_probe_local_replay_is_local_only() -> None:
    source = _read("src/context/source_candidate_external_probe_local_replay.py").lower()
    cli = _read("tools/source_candidate_external_probe_local_replay_cli.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "authorization")
    for forbidden_text in forbidden:
        assert forbidden_text not in source
        assert forbidden_text not in cli


def test_external_probe_local_replay_uses_audit_event_schema() -> None:
    source = _read("src/context/source_candidate_external_probe_local_replay.py")
    assert "missipy.source_candidate.external_probe_local_audit_event.v1" in source
    assert "ready_event_count" in source
    assert "blocked_event_count" in source


def test_external_probe_local_replay_manifest_uses_post_migration_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_18_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_external_probe_local_replay.py" in manifest


def test_external_probe_local_replay_does_not_add_dot_or_svg() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_18_CHANGED_FILES.md")
    assert ".dot" not in manifest
    assert ".svg" not in manifest
