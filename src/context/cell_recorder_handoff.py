from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from context.cell_observation_event import CellObservationEvent
from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import write_cell_snapshots_jsonl
from context.cell_snapshot_journal_reader import read_cell_snapshot_jsonl


CELL_RECORDER_HANDOFF_SCHEMA = "missipy.cell_recorder_handoff_dry_run.v1"


@dataclass(frozen=True, slots=True)
class CellRecorderHandoffDryRunResult:
    """Compatibility result for recorded observation input to cell journal output."""

    input_path: str
    output_path: str
    event_count: int
    snapshot_count: int
    replay_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_RECORDER_HANDOFF_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.event_count == self.snapshot_count == self.replay_count

    def to_json_dict(self) -> dict[str, object]:
        return {
            "errors": list(self.errors),
            "event_count": self.event_count,
            "input_path": self.input_path,
            "ok": self.ok,
            "output_path": self.output_path,
            "replay_count": self.replay_count,
            "schema": self.schema,
            "snapshot_count": self.snapshot_count,
        }


def read_recorded_cell_observation_events(
    path: Path,
    *,
    strict: bool = False,
) -> tuple[CellObservationEvent, ...]:
    events: list[CellObservationEvent] = []
    errors: list[str] = []

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    events.append(CellObservationEvent.from_json_line(stripped))
                except Exception as exc:
                    message = f"line {line_number}: {type(exc).__name__}: {exc}"
                    if strict:
                        raise ValueError(message) from exc
                    errors.append(message)
    except Exception:
        if strict:
            raise

    if errors and strict:
        raise ValueError("; ".join(errors))

    return tuple(events)


def derive_snapshots_for_handoff(events: tuple[CellObservationEvent, ...]) -> tuple[CellSnapshot, ...]:
    return tuple(event.to_cell_snapshot() for event in events)


def run_cell_recorder_handoff_dry_run(
    input_path: Path,
    output_path: Path,
    *,
    strict: bool = False,
) -> CellRecorderHandoffDryRunResult:
    errors: list[str] = []

    try:
        events = read_recorded_cell_observation_events(input_path, strict=strict)
    except Exception as exc:
        if strict:
            raise
        events = ()
        errors.append(f"read: {type(exc).__name__}: {exc}")

    snapshots = derive_snapshots_for_handoff(events)

    write_result = write_cell_snapshots_jsonl(output_path, snapshots, strict=strict)
    errors.extend(write_result.errors)

    replay_result = read_cell_snapshot_jsonl(output_path, strict=strict)
    errors.extend(replay_result.errors)

    if len(snapshots) != len(replay_result.snapshots):
        errors.append(
            f"snapshot/replay count mismatch: {len(snapshots)} != {len(replay_result.snapshots)}"
        )

    if [snapshot.cell_id for snapshot in snapshots] != [snapshot.cell_id for snapshot in replay_result.snapshots]:
        errors.append("snapshot/replay cell order mismatch")

    return CellRecorderHandoffDryRunResult(
        input_path=str(input_path),
        output_path=str(output_path),
        event_count=len(events),
        snapshot_count=len(snapshots),
        replay_count=len(replay_result.snapshots),
        errors=tuple(errors),
    )


def result_to_json(result: CellRecorderHandoffDryRunResult) -> str:
    return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True)
