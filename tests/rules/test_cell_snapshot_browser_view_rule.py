from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_browser_view_is_tool_boundary_only() -> None:
    source = _read("tools/cell_snapshot_browser_view_server.py")
    assert 'DEFAULT_BIND_HOST = "127.0.0.1"' in source
    assert 'BROWSER_VIEW_PATH = "/view.html"' in source
    assert 'CELL_STREAM_PATH = "/cells.sse"' in source
    assert "ThreadingHTTPServer" in source
    assert "EventSource" in source
    assert "<canvas" in source


def test_browser_view_has_no_command_or_external_api_path() -> None:
    source = _read("tools/cell_snapshot_browser_view_server.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_browser_view_docs_keep_read_only_window_boundary() -> None:
    doc = _read("doc/server/CELL_SNAPSHOT_BROWSER_CANVAS_VIEW.md")
    assert "read-only" in doc
    assert "browser window" in doc
    assert "same missipy.cell.v1 journal" in doc
    assert "No command channel" in doc
    assert "127.0.0.1" in doc
    assert "/view.html" in doc


def test_browser_view_manifest_has_no_new_dependency_or_remote_surface() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_3_BROWSER_CANVAS_READ_ONLY_CELL_VIEW.md")
    assert "tools/cell_snapshot_browser_view_server.py" in manifest
    assert "local browser window" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
