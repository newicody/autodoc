from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_github_adapter_is_fake_only_in_phase7_4() -> None:
    source = _read("src/context/source_candidate_github_adapter.py")
    assert "FakeSourceCandidateGithubProjectionAdapter" in source
    assert "fake_only=True" in source
    assert "never contacts GitHub" in source


def test_github_adapter_has_no_network_process_or_token_handling() -> None:
    source = _read("src/context/source_candidate_github_adapter.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "token", "authorization")
    for token in forbidden:
        assert token not in source


def test_github_adapter_requires_remote_mutation_gate() -> None:
    source = _read("src/context/source_candidate_github_adapter.py")
    assert "run_source_candidate_remote_mutation_gate" in source
    assert "SourceCandidateRemoteMutationGatePolicy" in source


def test_github_adapter_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_4_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_github_adapter.py" in manifest


def test_github_adapter_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/62_source_candidate_github_adapter_interface.dot"
    svg = ROOT / "doc/docs/architecture/context/62_source_candidate_github_adapter_interface.svg"
    assert dot.exists()
    assert not svg.exists()
