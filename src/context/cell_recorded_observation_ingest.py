from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from context.cell_observation_event import CellObservationEvent
from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import write_cell_snapshots_jsonl


CELL_RECORDED_OBSERVATION_INGEST_SCHEMA = "missipy.cell_recorded_observation_ingest.v1"
CELL_RECORDED_OBSERVATION_STATE_SCHEMA = "missipy.cell_recorded_observation_ingest_state.v1"


@dataclass(frozen=True, slots=True)
class CellRecordedObservationIngestState:
    source_path: str
    next_offset: int
    schema: str = CELL_RECORDED_OBSERVATION_STATE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CELL_RECORDED_OBSERVATION_STATE_SCHEMA:
            raise ValueError(f"unsupported recorded observation ingest state schema: {self.schema!r}")
        if self.next_offset < 0:
            raise ValueError("next_offset must be >= 0")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "next_offset": self.next_offset,
            "schema": self.schema,
            "source_path": self.source_path,
        }

    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "CellRecordedObservationIngestState":
        schema = str(mapping.get("schema", ""))
        if schema != CELL_RECORDED_OBSERVATION_STATE_SCHEMA:
            raise ValueError(f"unsupported recorded observation ingest state schema: {schema!r}")
        return cls(
            source_path=str(mapping["source_path"]),
            next_offset=int(mapping["next_offset"]),
            schema=schema,
        )


@dataclass(frozen=True, slots=True)
class CellRecordedObservationReadResult:
    source_path: str
    start_offset: int
    next_offset: int
    attempted_lines: int
    events: tuple[CellObservationEvent, ...]
    dropped_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_RECORDED_OBSERVATION_INGEST_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "attempted_lines": self.attempted_lines,
            "dropped_count": self.dropped_count,
            "errors": list(self.errors),
            "event_count": len(self.events),
            "next_offset": self.next_offset,
            "schema": self.schema,
            "source_path": self.source_path,
            "start_offset": self.start_offset,
        }


@dataclass(frozen=True, slots=True)
class CellRecordedObservationIngestResult:
    source_path: str
    journal_path: str
    state_path: str
    start_offset: int
    next_offset: int
    attempted_lines: int
    event_count: int
    snapshot_count: int
    written_count: int
    dropped_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_RECORDED_OBSERVATION_INGEST_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.event_count == self.snapshot_count == self.written_count

    def to_json_dict(self) -> dict[str, object]:
        return {
            "attempted_lines": self.attempted_lines,
            "dropped_count": self.dropped_count,
            "errors": list(self.errors),
            "event_count": self.event_count,
            "journal_path": self.journal_path,
            "next_offset": self.next_offset,
            "ok": self.ok,
            "schema": self.schema,
            "snapshot_count": self.snapshot_count,
            "source_path": self.source_path,
            "start_offset": self.start_offset,
            "state_path": self.state_path,
            "written_count": self.written_count,
        }


def load_recorded_observation_ingest_state(
    state_path: Path,
    *,
    source_path: Path,
) -> CellRecordedObservationIngestState:
    if not state_path.exists():
        return CellRecordedObservationIngestState(source_path=str(source_path), next_offset=0)

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("recorded observation ingest state must be a JSON object")

    state = CellRecordedObservationIngestState.from_mapping(payload)
    if state.source_path != str(source_path):
        return CellRecordedObservationIngestState(source_path=str(source_path), next_offset=0)
    return state


def save_recorded_observation_ingest_state(
    state_path: Path,
    state: CellRecordedObservationIngestState,
) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_recorded_observation_events_from_offset(
    source_path: Path,
    *,
    offset: int = 0,
    max_lines: int | None = None,
    strict: bool = False,
) -> CellRecordedObservationReadResult:
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if max_lines is not None and max_lines <= 0:
        raise ValueError("max_lines must be > 0")

    events: list[CellObservationEvent] = []
    errors: list[str] = []
    dropped_count = 0
    attempted_lines = 0
    next_offset = offset

    if not source_path.exists():
        message = f"source does not exist: {source_path}"
        if strict:
            raise FileNotFoundError(message)
        return CellRecordedObservationReadResult(
            source_path=str(source_path),
            start_offset=offset,
            next_offset=offset,
            attempted_lines=0,
            events=(),
            dropped_count=0,
            errors=(message,),
        )

    with source_path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        while True:
            if max_lines is not None and attempted_lines >= max_lines:
                break

            line = handle.readline()
            if not line:
                break

            next_offset = handle.tell()
            stripped = line.strip()
            if not stripped:
                continue

            attempted_lines += 1
            try:
                events.append(CellObservationEvent.from_json_line(stripped))
            except Exception as exc:
                message = f"line {attempted_lines}: {type(exc).__name__}: {exc}"
                if strict:
                    raise ValueError(message) from exc
                dropped_count += 1
                errors.append(message)

    return CellRecordedObservationReadResult(
        source_path=str(source_path),
        start_offset=offset,
        next_offset=next_offset,
        attempted_lines=attempted_lines,
        events=tuple(events),
        dropped_count=dropped_count,
        errors=tuple(errors),
    )


def derive_snapshots_from_recorded_events(
    events: tuple[CellObservationEvent, ...],
) -> tuple[CellSnapshot, ...]:
    return tuple(event.to_cell_snapshot() for event in events)


def ingest_recorded_observation_events_to_cell_journal(
    source_path: Path,
    journal_path: Path,
    state_path: Path,
    *,
    max_lines: int | None = None,
    strict: bool = False,
) -> CellRecordedObservationIngestResult:
    state = load_recorded_observation_ingest_state(state_path, source_path=source_path)
    read_result = read_recorded_observation_events_from_offset(
        source_path,
        offset=state.next_offset,
        max_lines=max_lines,
        strict=strict,
    )
    snapshots = derive_snapshots_from_recorded_events(read_result.events)
    write_result = write_cell_snapshots_jsonl(journal_path, snapshots, strict=strict)

    errors = list(read_result.errors)
    errors.extend(write_result.errors)

    next_state = CellRecordedObservationIngestState(
        source_path=str(source_path),
        next_offset=read_result.next_offset,
    )
    save_recorded_observation_ingest_state(state_path, next_state)

    return CellRecordedObservationIngestResult(
        source_path=str(source_path),
        journal_path=str(journal_path),
        state_path=str(state_path),
        start_offset=read_result.start_offset,
        next_offset=read_result.next_offset,
        attempted_lines=read_result.attempted_lines,
        event_count=len(read_result.events),
        snapshot_count=len(snapshots),
        written_count=write_result.written_count,
        dropped_count=read_result.dropped_count + write_result.dropped_count,
        errors=tuple(errors),
    )
