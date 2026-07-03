from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase10_closure_lists_all_local_view_modes() -> None:
    doc = _read("doc/reports/phase10/PART10_CELL_LENS_LOCAL_UI_CLOSURE_REPORT.md")
    assert "VisPy desktop" in doc
    assert "browser Canvas" in doc
    assert "browser health Canvas" in doc
    assert "SSE stream" in doc
    assert "127.0.0.1" in doc


def test_phase10_closure_preserves_read_only_invariant() -> None:
    doc = _read("doc/reports/phase10/PART10_CELL_LENS_LOCAL_UI_CLOSURE_REPORT.md")
    assert "visualization is a lens, not a lever" in doc
    assert "No Phase 10 browser or SSE path may command the system" in doc
    assert "no browser command channel" in doc
    assert "no EventBus command channel" in doc
    assert "no Scheduler command from visualization" in doc


def test_local_ui_runbook_contains_repeatable_commands() -> None:
    doc = _read("doc/runbooks/CELL_LENS_LOCAL_UI_RUNBOOK.md")
    assert "tools/cell_lens_local_demo_bundle.py" in doc
    assert "tools/visualize_cell_population_vispy.py" in doc
    assert "QT_QPA_PLATFORM=wayland" in doc
    assert "tools/cell_snapshot_sse_server.py" in doc
    assert "tools/cell_snapshot_browser_view_server.py" in doc
    assert "tools/cell_snapshot_browser_health_view_server.py" in doc
    assert "tools/cell_lens_all_view_launch_profiles.py" in doc


def test_next_handoff_moves_back_to_recorded_observation_production() -> None:
    doc = _read("doc/maintenance/CELL_LENS_NEXT_HANDOFF_AFTER_PHASE10.md")
    assert "recorded observation producer" in doc
    assert "journal writer integration" in doc
    assert "replay compatibility checks" in doc
    assert "typed command → Scheduler" in doc
    assert "events → snapshots → journal → views" in doc


def test_phase10_closure_manifest_has_no_runtime_changes() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_8_CELL_LENS_PHASE10_CLOSURE_RUNBOOK.md")
    assert "Runtime changes" in manifest
    assert "None" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
