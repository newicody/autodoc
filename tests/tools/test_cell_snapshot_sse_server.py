from __future__ import annotations

from pathlib import Path
import sys

import pytest

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import CellSnapshotJournalWriter


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from cell_snapshot_sse_server import (  # noqa: E402
    CELL_STREAM_PATH,
    DEFAULT_BIND_HOST,
    HEALTH_PATH,
    build_replay_sse_text,
    make_cell_sse_handler,
    serve_cell_sse,
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


def _snapshot(index: int) -> CellSnapshot:
    return CellSnapshot(
        cell_id=f"cell-{index}",
        source_class="scheduler.short_task",
        score=1.0,
        age=float(index),
        cost=0.5,
        lifecycle_state="completed",
        observed_at=f"2026-07-03T10:00:0{index}Z",
    )


def test_build_replay_sse_text_uses_existing_journal(tmp_path: Path) -> None:
    journal = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(journal).append_many([_snapshot(1), _snapshot(2)])

    text = build_replay_sse_text(journal, limit=1)

    assert text.startswith("id: 0\nevent: cell_snapshot\ndata: ")
    assert "cell-1" in text
    assert "cell-2" not in text


def test_make_cell_sse_handler_exposes_expected_paths(tmp_path: Path) -> None:
    handler = make_cell_sse_handler(journal=tmp_path / "cells.jsonl")

    assert handler.server_version == "MissiPyCellSse/0.1"
    assert CELL_STREAM_PATH == "/cells.sse"
    assert HEALTH_PATH == "/health"


def test_serve_cell_sse_is_local_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local-only"):
        serve_cell_sse(journal=tmp_path / "cells.jsonl", host="0.0.0.0", server_factory=FakeServer)


def test_serve_cell_sse_uses_local_default_host(tmp_path: Path) -> None:
    FakeServer.created_with = None
    FakeServer.served = False
    FakeServer.closed = False

    serve_cell_sse(journal=tmp_path / "cells.jsonl", server_factory=FakeServer)

    assert FakeServer.created_with is not None
    assert FakeServer.created_with[0] == (DEFAULT_BIND_HOST, 8765)
    assert FakeServer.served is True
    assert FakeServer.closed is True
