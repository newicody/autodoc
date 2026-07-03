from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_cell_snapshot_sse_server_is_tool_boundary_only() -> None:
    source = _read("tools/cell_snapshot_sse_server.py")
    assert 'DEFAULT_BIND_HOST = "127.0.0.1"' in source
    assert 'CELL_STREAM_PATH = "/cells.sse"' in source
    assert "ThreadingHTTPServer" in source
    assert "METHOD_NOT_ALLOWED" in source


def test_cell_snapshot_sse_server_has_no_command_or_external_api_path() -> None:
    source = _read("tools/cell_snapshot_sse_server.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_cell_snapshot_sse_server_docs_keep_read_only_local_boundary() -> None:
    doc = _read("doc/server/CELL_SNAPSHOT_SSE_LOCAL_ENDPOINT.md")
    assert "read-only" in doc
    assert "127.0.0.1" in doc
    assert "/cells.sse" in doc
    assert "same missipy.cell.v1 journal" in doc
    assert "No POST" in doc
    assert "No command channel" in doc


def test_cell_snapshot_sse_server_manifest_declares_endpoint_but_no_mobile_source_of_truth() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_2_LOCAL_READ_ONLY_SSE_ENDPOINT.md")
    assert "tools/cell_snapshot_sse_server.py" in manifest
    assert "local read-only endpoint" in manifest
    assert "mobile source of truth" not in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
