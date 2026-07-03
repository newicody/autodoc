from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_snapshot_sse_contract_declares_versioned_schema() -> None:
    source = _read("src/context/cell_snapshot_sse.py")
    assert 'CELL_SNAPSHOT_SSE_SCHEMA = "missipy.cell_snapshot_sse.v1"' in source
    assert 'CELL_SNAPSHOT_SSE_EVENT_NAME = "cell_snapshot"' in source
    assert "CellSnapshotSseEvent" in source


def test_cell_snapshot_sse_contract_has_no_server_or_command_path() -> None:
    source = _read("src/context/cell_snapshot_sse.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github", "socketserver"]
    for token in forbidden:
        assert token not in source


def test_cell_snapshot_sse_contract_docs_keep_mobile_read_only() -> None:
    doc = _read("doc/contracts/CELL_SNAPSHOT_SSE_STREAM_CONTRACT_V1.md")
    assert "missipy.cell_snapshot_sse.v1" in doc
    assert "read-only" in doc
    assert "same missipy.cell.v1 journal" in doc
    assert "no command channel" in doc
    assert "local server" in doc
    assert "Phase 10" in doc


def test_cell_snapshot_sse_contract_manifest_has_no_runtime_server() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_1_CELL_SNAPSHOT_SSE_STREAM_CONTRACT.md")
    assert "src/context/cell_snapshot_sse.py" in manifest
    assert "tools/cell_snapshot_sse_dry_run.py" in manifest
    assert "server endpoint" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
