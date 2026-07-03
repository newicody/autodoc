from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal_reader import read_cell_snapshot_jsonl


CELL_SNAPSHOT_SSE_SCHEMA = "missipy.cell_snapshot_sse.v1"
CELL_SNAPSHOT_SSE_EVENT_NAME = "cell_snapshot"


@dataclass(frozen=True, slots=True)
class CellSnapshotSseEvent:
    """Renderer-neutral SSE event for read-only cell snapshot streaming."""

    event_id: str
    data: CellSnapshot
    event_name: str = CELL_SNAPSHOT_SSE_EVENT_NAME
    schema: str = CELL_SNAPSHOT_SSE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CELL_SNAPSHOT_SSE_SCHEMA:
            raise ValueError(f"unsupported cell snapshot SSE schema: {self.schema!r}")
        if not self.event_id:
            raise ValueError("event_id must be non-empty")
        if self.event_name != CELL_SNAPSHOT_SSE_EVENT_NAME:
            raise ValueError(f"unsupported event_name: {self.event_name!r}")

    def to_sse_text(self) -> str:
        payload = {
            "schema": self.schema,
            "snapshot": self.data.to_json_dict(),
        }
        return format_sse_event(
            event_name=self.event_name,
            event_id=self.event_id,
            data=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        )


def format_sse_event(*, event_name: str, event_id: str, data: str) -> str:
    if "\n" in event_name or "\n" in event_id:
        raise ValueError("SSE event name and id must be single-line values")

    lines = [
        f"id: {event_id}",
        f"event: {event_name}",
    ]

    for data_line in data.splitlines() or [""]:
        lines.append(f"data: {data_line}")

    return "\n".join(lines) + "\n\n"


def snapshot_to_sse_event(snapshot: CellSnapshot, *, sequence: int) -> CellSnapshotSseEvent:
    if sequence < 0:
        raise ValueError("sequence must be >= 0")
    return CellSnapshotSseEvent(event_id=str(sequence), data=snapshot)


def snapshots_to_sse_text(snapshots: Iterable[CellSnapshot], *, start_sequence: int = 0) -> str:
    if start_sequence < 0:
        raise ValueError("start_sequence must be >= 0")

    chunks: list[str] = []
    for offset, snapshot in enumerate(snapshots):
        chunks.append(snapshot_to_sse_event(snapshot, sequence=start_sequence + offset).to_sse_text())
    return "".join(chunks)


def cell_journal_to_sse_text(path: object, *, limit: int | None = None, start_sequence: int = 0) -> str:
    """Convert a cell snapshot JSONL journal to read-only SSE text.

    This helper does not open a socket. It exists so Phase 10 can validate the
    stream contract before adding a local server endpoint.
    """

    result = read_cell_snapshot_jsonl(path, limit=limit)  # type: ignore[arg-type]
    return snapshots_to_sse_text(result.snapshots, start_sequence=start_sequence)
