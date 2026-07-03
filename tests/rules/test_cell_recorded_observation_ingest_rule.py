from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_recorded_observation_ingest_declares_versioned_schema() -> None:
    source = _read("src/context/cell_recorded_observation_ingest.py")
    assert 'CELL_RECORDED_OBSERVATION_INGEST_SCHEMA = "missipy.cell_recorded_observation_ingest.v1"' in source
    assert 'CELL_RECORDED_OBSERVATION_STATE_SCHEMA = "missipy.cell_recorded_observation_ingest_state.v1"' in source
    assert "ingest_recorded_observation_events_to_cell_journal" in source


def test_recorded_observation_ingest_has_no_command_or_network_path() -> None:
    source = _read("src/context/cell_recorded_observation_ingest.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_recorded_observation_ingest_docs_keep_observation_boundary() -> None:
    doc = _read("doc/contracts/CELL_RECORDED_OBSERVATION_INGEST_V1.md")
    assert "missipy.cell_recorded_observation_ingest.v1" in doc
    assert "missipy.cell_observation_event.v1" in doc
    assert "missipy.cell.v1 journal" in doc
    assert "offset state" in doc
    assert "observation-only" in doc
    assert "not a command path" in doc


def test_recorded_observation_ingest_manifest_has_no_ui_or_network_dependency() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART11_1_RECORDED_OBSERVATION_INGEST_TO_CELL_JOURNAL.md")
    assert "src/context/cell_recorded_observation_ingest.py" in manifest
    assert "tools/ingest_recorded_observations_to_cell_journal.py" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
