from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_lens_roadmap_places_steps_in_phases() -> None:
    doc = _read("doc/maintenance/ROADMAP_B_CELL_LENS_INSERTION.md")
    assert "Phase 8" in doc
    assert "missipy.cell.v1" in doc
    assert "Phase 9" in doc
    assert "VisPy" in doc
    assert "Phase 10" in doc
    assert "SSE" in doc
    assert "out of scope" in doc


def test_cell_lens_architecture_keeps_lens_and_lever_separate() -> None:
    doc = _read("doc/docs/architecture/CELL_LENS_ARCHITECTURE.md")
    assert "Lens, not lever" in doc
    assert "Observation:" in doc
    assert "Command:" in doc
    assert "typed command" in doc
    assert "Scheduler" in doc
    assert "must not command the system" in doc


def test_cell_lens_rules_forbid_eventbus_commands() -> None:
    rules = _read("doc/code-rules/CELL_LENS_OBSERVATION_RULES.md")
    assert "EventBus is not a command channel" in rules
    assert "typed command" in rules
    assert "Scheduler" in rules
    assert "missipy.cell.v1" in rules


def test_cell_lens_rules_confine_vispy_to_boundary() -> None:
    rules = _read("doc/code-rules/CELL_LENS_OBSERVATION_RULES.md")
    assert "Kernel, Scheduler, EventBus core, contracts, and replay core must not import" in rules
    assert "VisPy" in rules


def test_cell_lens_health_is_not_raw_duration() -> None:
    architecture = _read("doc/docs/architecture/CELL_LENS_ARCHITECTURE.md")
    rules = _read("doc/code-rules/CELL_LENS_OBSERVATION_RULES.md")
    assert "Health is not raw speed" in architecture
    assert "expected lifecycle" in architecture
    assert "expected lifecycle" in rules


def test_cell_lens_manifest_has_no_runtime_or_svg_changes() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_2_ROADMAP_B_CELL_LENS_ARCHITECTURE_UPDATE.md")
    assert "Runtime changes" in manifest
    assert "None" in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
