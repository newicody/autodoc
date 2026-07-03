from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from cell_snapshot_browser_health_view_server import (  # noqa: E402
    BROWSER_HEALTH_VIEW_HTML,
    CELL_STREAM_PATH,
    DEFAULT_BIND_HOST,
    HEALTH_VIEW_PATH,
    ROOT_VIEW_PATH,
    make_browser_health_view_handler,
    serve_browser_health_cell_view,
)


class FakeServer:
    created_with: tuple[object, object] | None = None
    served = False
    closed = False

    def __init__(self, address: object, handler: object) -> None:
        self.__class__.created_with = (address, handler)

    def serve_forever(self) -> None:
        self.__class__.served = True

    def server_close(self) -> None:
        self.__class__.closed = True


def test_browser_health_view_html_uses_canvas_eventsource_and_legend() -> None:
    assert "<canvas" in BROWSER_HEALTH_VIEW_HTML
    assert 'new EventSource("/cells.sse")' in BROWSER_HEALTH_VIEW_HTML
    assert "statusFor" in BROWSER_HEALTH_VIEW_HTML
    assert "healthyCount" in BROWSER_HEALTH_VIEW_HTML
    assert "degradedCount" in BROWSER_HEALTH_VIEW_HTML
    assert "fetch(" not in BROWSER_HEALTH_VIEW_HTML
    assert "XMLHttpRequest" not in BROWSER_HEALTH_VIEW_HTML


def test_browser_health_view_handler_exposes_expected_paths(tmp_path: Path) -> None:
    handler = make_browser_health_view_handler(journal=tmp_path / "cells.jsonl")

    assert handler.server_version == "MissiPyCellBrowserHealthView/0.1"
    assert ROOT_VIEW_PATH == "/"
    assert HEALTH_VIEW_PATH == "/health-view.html"
    assert CELL_STREAM_PATH == "/cells.sse"


def test_browser_health_view_server_is_local_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local-only"):
        serve_browser_health_cell_view(journal=tmp_path / "cells.jsonl", host="0.0.0.0", server_factory=FakeServer)


def test_browser_health_view_server_uses_default_local_host(tmp_path: Path) -> None:
    FakeServer.created_with = None
    FakeServer.served = False
    FakeServer.closed = False

    serve_browser_health_cell_view(journal=tmp_path / "cells.jsonl", server_factory=FakeServer)

    assert FakeServer.created_with is not None
    assert FakeServer.created_with[0] == (DEFAULT_BIND_HOST, 8767)
    assert FakeServer.served is True
    assert FakeServer.closed is True
