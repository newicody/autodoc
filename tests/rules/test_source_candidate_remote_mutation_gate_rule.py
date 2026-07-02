from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_remote_mutation_gate_is_closed_by_default() -> None:
    source = _read("src/context/source_candidate_remote_mutation_gate.py")
    assert "remote_mutation_enabled: bool = False" in source
    assert "operator_confirmed: bool = False" in source
    assert "allowed_repositories: tuple[str, ...] = ()" in source


def test_remote_mutation_gate_has_no_network_or_process_calls() -> None:
    source = _read("src/context/source_candidate_remote_mutation_gate.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "github_api")
    for token in forbidden:
        assert token not in source


def test_remote_mutation_gate_does_not_modify_scheduler() -> None:
    manifest = _read("MANIFEST_PHASE7_3_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_remote_mutation_gate.py" in manifest


def test_remote_mutation_gate_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/61_source_candidate_remote_mutation_gate.dot"
    svg = ROOT / "doc/docs/architecture/context/61_source_candidate_remote_mutation_gate.svg"
    assert dot.exists()
    assert not svg.exists()
