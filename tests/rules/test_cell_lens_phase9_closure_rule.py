from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_lens_phase9_closure_lists_closed_chain() -> None:
    doc = _read("doc/reports/phase9/PART9_CELL_LENS_CLOSURE_REPORT.md")
    assert "missipy.cell.v1" in doc
    assert "cell snapshot JSONL journal" in doc
    assert "replay/tail reader" in doc
    assert "synthetic population generator" in doc
    assert "VisPy desktop viewer" in doc
    assert "recorded observation adapter" in doc
    assert "recorder handoff dry-run" in doc


def test_cell_lens_phase9_closure_keeps_lens_not_lever() -> None:
    doc = _read("doc/reports/phase9/PART9_CELL_LENS_CLOSURE_REPORT.md")
    assert "visualization is a lens, not a lever" in doc
    assert "Observation:" in doc
    assert "Command:" in doc
    assert "typed command" in doc
    assert "Scheduler" in doc


def test_cell_lens_phase9_handoff_allows_only_phase10_read_only_mobile_window() -> None:
    doc = _read("doc/maintenance/CELL_LENS_PHASE9_HANDOFF.md")
    assert "Phase 10 may add" in doc
    assert "local server" in doc
    assert "SSE stream" in doc
    assert "browser view" in doc
    assert "The stream must read the same journal" in doc
    assert "browser command channel" in doc
    assert "mobile source of truth" in doc


def test_cell_lens_phase9_handoff_forbids_observation_command_paths() -> None:
    doc = _read("doc/maintenance/CELL_LENS_PHASE9_HANDOFF.md")
    assert "typed command submitted to" in doc
    assert "Scheduler" in doc
    assert "must not travel through the EventBus" in doc
    assert "journal" in doc
    assert "SSE stream" in doc


def test_cell_lens_phase9_closure_manifest_has_no_runtime_changes() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART9_4_CELL_LENS_PHASE9_CLOSURE_HANDOFF.md")
    assert "Runtime changes" in manifest
    assert "None" in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
    assert "requirements" not in manifest
