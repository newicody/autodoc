from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_projection_bundle_is_local_only() -> None:
    source = _read("src/context/source_candidate_projection_bundle.py").lower()
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    for token in forbidden:
        assert token not in source


def test_projection_bundle_is_additive_and_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE6_14_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_projection_bundle.py" in manifest


def test_projection_bundle_has_dot_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/54_source_candidate_projection_bundle.dot"
    svg = ROOT / "doc/docs/architecture/context/54_source_candidate_projection_bundle.svg"
    assert dot.exists()
    assert not svg.exists()
