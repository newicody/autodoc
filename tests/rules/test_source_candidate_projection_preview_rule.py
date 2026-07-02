from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_projection_preview_is_local_and_additive() -> None:
    source = _read("src/context/source_candidate_projection_preview.py").lower()
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    for token in forbidden:
        assert token not in source


def test_projection_preview_does_not_modify_scheduler() -> None:
    manifest = _read("MANIFEST_PHASE6_13_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_projection_preview.py" in manifest


def test_projection_preview_has_architecture_source_only() -> None:
    assert (ROOT / "doc/docs/architecture/context/53_source_candidate_projection_preview.dot").exists()
    assert not (ROOT / "doc/docs/architecture/context/53_source_candidate_projection_preview.svg").exists()
