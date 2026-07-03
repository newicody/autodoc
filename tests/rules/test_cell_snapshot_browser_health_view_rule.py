from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_browser_health_view_is_tool_boundary_only() -> None:
    source = _read("tools/cell_snapshot_browser_health_view_server.py")
    assert 'DEFAULT_BIND_HOST = "127.0.0.1"' in source
    assert 'HEALTH_VIEW_PATH = "/health-view.html"' in source
    assert 'CELL_STREAM_PATH = "/cells.sse"' in source
    assert "EventSource" in source
    assert "<canvas" in source
    assert "statusFor" in source


def test_browser_health_view_has_no_command_or_external_api_path() -> None:
    source = _read("tools/cell_snapshot_browser_health_view_server.py")
    forbidden = ["vispy", "Scheduler", "EventBus", "requests", "urllib", "httpx", "OPENAI_API_KEY", "github"]
    for token in forbidden:
        assert token not in source


def test_browser_health_view_docs_keep_read_only_health_boundary() -> None:
    doc = _read("doc/server/CELL_SNAPSHOT_BROWSER_CANVAS_HEALTH_VIEW.md")
    assert "read-only" in doc
    assert "health view" in doc
    assert "same missipy.cell.v1 journal" in doc
    assert "No command channel" in doc
    assert "127.0.0.1" in doc
    assert "/health-view.html" in doc


def test_browser_health_view_manifest_has_no_dependency_or_remote_surface() -> None:
    manifest = _read("doc/manifests/MANIFEST_PART10_6_BROWSER_CANVAS_HEALTH_VIEW.md")
    assert "tools/cell_snapshot_browser_health_view_server.py" in manifest
    assert "browser Canvas health view" in manifest
    assert "requirements" not in manifest
    assert ".dot" not in manifest
    assert ".svg" not in manifest
