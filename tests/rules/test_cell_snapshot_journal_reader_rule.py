from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_snapshot_journal_reader_declares_versioned_schema() -> None:
    source = _read("src/context/cell_snapshot_journal_reader.py")
    assert 'CELL_SNAPSHOT_JOURNAL_READER_SCHEMA = "missipy.cell_snapshot_journal_reader.v1"' in source
    assert "CellSnapshotJournalReadResult" in source
    assert "CellSnapshotJournalTailResult" in source


def test_cell_snapshot_journal_reader_is_observation_only() -> None:
    source = _read("src/context/cell_snapshot_journal_reader.py")
    forbidden = [
        "vispy",
        "Scheduler",
        "EventBus",
        "requests",
        "urllib",
        "httpx",
        "subprocess",
        "OPENAI_API_KEY",
    ]
    for token in forbidden:
        assert token not in source


def test_cell_snapshot_journal_reader_documents_replay_and_tail() -> None:
    doc = _read("doc/contracts/CELL_SNAPSHOT_JOURNAL_READER_CONTRACT_V1.md")
    assert "missipy.cell_snapshot_journal_reader.v1" in doc
    assert "replay" in doc
    assert "tail" in doc
    assert "non-blocking" in doc
    assert "Live mode is replay that has caught up" in doc


def test_cell_snapshot_journal_reader_manifest_has_no_renderer_or_network() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_5_CELL_SNAPSHOT_JOURNAL_REPLAY_TAIL_READER.md")
    assert "src/context/cell_snapshot_journal_reader.py" in manifest
    assert "VisPy" not in manifest
    assert "SSE" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
