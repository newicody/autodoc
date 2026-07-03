from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_recorder_handoff_declares_versioned_schema() -> None:
    source = _read("src/context/cell_recorder_handoff.py")
    assert 'CELL_RECORDER_HANDOFF_SCHEMA = "missipy.cell_recorder_handoff_dry_run.v1"' in source
    assert "run_cell_recorder_handoff_dry_run" in source


def test_cell_recorder_handoff_is_file_dry_run_only() -> None:
    source = _read("src/context/cell_recorder_handoff.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_cell_recorder_handoff_docs_keep_no_live_subscription() -> None:
    doc = _read("doc/contracts/CELL_RECORDER_HANDOFF_DRY_RUN_V1.md")
    assert "missipy.cell_recorder_handoff_dry_run.v1" in doc
    assert "dry-run" in doc
    assert "no live subscription" in doc
    assert "not a command path" in doc
    assert "same missipy.cell.v1 journal" in doc


def test_cell_recorder_handoff_manifest_has_no_renderer_or_network() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART9_3_CELL_RECORDER_HANDOFF_DRY_RUN.md")
    assert "src/context/cell_recorder_handoff.py" in manifest
    assert "tools/cell_recorder_handoff_dry_run.py" in manifest
    assert "VisPy" not in manifest
    assert "SSE" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
