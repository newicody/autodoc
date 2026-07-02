from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_github_projection_payload_is_dry_run_only() -> None:
    source = _read("src/context/source_candidate_github_projection_payload.py")
    assert "dry_run=True" in source
    assert "remote_mutation=False" in source
    assert "No remote mutation has been performed." in source


def test_github_projection_payload_has_no_network_or_process_calls() -> None:
    source = _read("src/context/source_candidate_github_projection_payload.py").lower()
    forbidden = ("requests", "urllib", "httpx", "subprocess", "gh ")
    for token in forbidden:
        assert token not in source


def test_github_projection_payload_does_not_modify_scheduler() -> None:
    manifest = _read("doc/manifests/MANIFEST_PHASE7_2_CHANGED_FILES.md")
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/context/source_candidate_github_projection_payload.py" in manifest


def test_github_projection_payload_has_architecture_source_only() -> None:
    dot = ROOT / "doc/docs/architecture/context/60_source_candidate_github_projection_payload.dot"
    svg = ROOT / "doc/docs/architecture/context/60_source_candidate_github_projection_payload.svg"
    assert dot.exists()
    assert not svg.exists()
