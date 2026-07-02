from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_handoff_dry_run_is_local_only() -> None:
    source = _read("src/context/source_candidate_projection_handoff_dry_run.py").lower()
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    for token in forbidden:
        assert token not in source


def test_handoff_dry_run_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE6_17_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_projection_handoff_dry_run.py" in manifest


def test_handoff_dry_run_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/57_source_candidate_projection_handoff_dry_run.dot"
    svg = ROOT / "doc/docs/architecture/context/57_source_candidate_projection_handoff_dry_run.svg"
    assert dot.exists()
    assert not svg.exists()
