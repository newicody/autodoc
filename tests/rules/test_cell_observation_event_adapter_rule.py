from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_observation_event_adapter_declares_versioned_schema() -> None:
    source = _read("src/context/cell_observation_event.py")
    assert 'CELL_OBSERVATION_EVENT_SCHEMA = "missipy.cell_observation_event.v1"' in source
    assert "CellObservationEvent" in source
    assert "to_cell_snapshot" in source


def test_cell_observation_event_adapter_is_observation_only() -> None:
    source = _read("src/context/cell_observation_event.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_cell_observation_event_adapter_docs_keep_lens_and_lever_separate() -> None:
    doc = _read("doc/contracts/CELL_OBSERVATION_EVENT_ADAPTER_V1.md")
    assert "missipy.cell_observation_event.v1" in doc
    assert "observation-only" in doc
    assert "not a command" in doc
    assert "EventBus / recorder" in doc
    assert "typed command" in doc
    assert "Scheduler" in doc


def test_cell_observation_event_adapter_manifest_has_no_renderer_or_network() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART9_2_CELL_OBSERVATION_EVENT_ADAPTER.md")
    assert "src/context/cell_observation_event.py" in manifest
    assert "tools/convert_cell_observation_events.py" in manifest
    assert "VisPy" not in manifest
    assert "SSE" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
