from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_external_projection_contract_is_local_only() -> None:
    source = _read("src/context/source_candidate_external_projection_contract.py").lower()
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    for token in forbidden:
        assert token not in source


def test_external_projection_contract_is_target_neutral() -> None:
    source = _read("src/context/source_candidate_external_projection_contract.py")
    assert "github_project_surface" not in source
    assert "generic_project_surface" in source


def test_external_projection_contract_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_1_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_external_projection_contract.py" in manifest


def test_external_projection_contract_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/59_source_candidate_external_projection_contract.dot"
    svg = ROOT / "doc/docs/architecture/context/59_source_candidate_external_projection_contract.svg"
    assert dot.exists()
    assert not svg.exists()
