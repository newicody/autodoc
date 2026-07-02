from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_github_export_bundle_is_local_only() -> None:
    source = _read("src/context/source_candidate_github_export_bundle.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for token in forbidden:
        assert token not in source


def test_github_export_bundle_uses_fake_adapter_and_gate() -> None:
    source = _read("src/context/source_candidate_github_export_bundle.py")
    assert "FakeSourceCandidateGithubProjectionAdapter" in source
    assert "run_source_candidate_remote_mutation_gate" in source


def test_github_export_bundle_does_not_modify_scheduler() -> None:
    manifest = _read("MANIFEST_PHASE7_5_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_github_export_bundle.py" in manifest


def test_github_export_bundle_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/63_source_candidate_github_export_bundle.dot"
    svg = ROOT / "doc/docs/architecture/context/63_source_candidate_github_export_bundle.svg"
    assert dot.exists()
    assert not svg.exists()
