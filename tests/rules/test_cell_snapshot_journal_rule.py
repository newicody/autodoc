from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_snapshot_journal_declares_versioned_journal_schema() -> None:
    source = _read("src/context/cell_snapshot_journal.py")
    assert 'CELL_SNAPSHOT_JOURNAL_SCHEMA = "missipy.cell_snapshot_journal.v1"' in source
    assert "CellSnapshotJournalWriter" in source
    assert "CellSnapshotJournalWriteResult" in source


def test_cell_snapshot_journal_is_boundary_only() -> None:
    source = _read("src/context/cell_snapshot_journal.py")
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


def test_cell_snapshot_journal_documentation_keeps_observation_and_command_separate() -> None:
    doc = _read("doc/contracts/CELL_SNAPSHOT_JOURNAL_CONTRACT_V1.md")
    assert "missipy.cell_snapshot_journal.v1" in doc
    assert "best-effort" in doc
    assert "EventBus / recorder / replay" in doc
    assert "not a command path" in doc
    assert "must not block the Scheduler" in doc


def test_cell_snapshot_journal_manifest_has_no_renderer_dependency() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART8_4_CELL_SNAPSHOT_JSONL_JOURNAL.md")
    assert "src/context/cell_snapshot_journal.py" in manifest
    assert "VisPy" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
