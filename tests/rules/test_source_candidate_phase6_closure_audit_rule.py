from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase6_closure_audit_is_local_only() -> None:
    source = _read("src/context/source_candidate_phase6_closure_audit.py").lower()
    forbidden = ("requests", "qdrant", "openvino", "subprocess")
    for token in forbidden:
        assert token not in source


def test_phase6_closure_audit_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE6_18_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_phase6_closure_audit.py" in manifest


def test_phase6_closure_audit_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/58_source_candidate_phase6_closure_audit.dot"
    svg = ROOT / "doc/docs/architecture/context/58_source_candidate_phase6_closure_audit.svg"
    assert dot.exists()
    assert not svg.exists()
