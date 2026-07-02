from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_read_only_external_probe_has_no_network_or_process_calls() -> None:
    source = _read("src/context/source_candidate_read_only_external_probe.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for token in forbidden:
        assert token not in source


def test_read_only_external_probe_is_fake_only_in_phase7_9() -> None:
    source = _read("src/context/source_candidate_read_only_external_probe.py")
    assert "FakeSourceCandidateReadOnlyExternalProbeAdapter" in source
    assert "external_call_performed=False" in source
    assert "read_only=True" in source


def test_read_only_external_probe_uses_post_migration_manifest_path() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_9_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_read_only_external_probe.py" in manifest


def test_read_only_external_probe_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/65_source_candidate_read_only_external_probe.dot"
    svg = ROOT / "doc/docs/architecture/context/65_source_candidate_read_only_external_probe.svg"
    assert dot.exists()
    assert not svg.exists()
