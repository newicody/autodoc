from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from context.cell_snapshot import CellSnapshot


CELL_SNAPSHOT_JOURNAL_READER_SCHEMA = "missipy.cell_snapshot_journal_reader.v1"


@dataclass(frozen=True, slots=True)
class CellSnapshotJournalReadResult:
    """Best-effort replay read result for a cell snapshot JSONL journal."""

    path: str
    attempted_lines: int
    snapshots: tuple[CellSnapshot, ...]
    dropped_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_SNAPSHOT_JOURNAL_READER_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.dropped_count == 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "attempted_lines": self.attempted_lines,
            "dropped_count": self.dropped_count,
            "errors": list(self.errors),
            "path": self.path,
            "schema": self.schema,
            "snapshot_count": len(self.snapshots),
        }


@dataclass(frozen=True, slots=True)
class CellSnapshotJournalTailResult:
    """Non-blocking tail read result for a cell snapshot JSONL journal."""

    path: str
    start_offset: int
    next_offset: int
    attempted_lines: int
    snapshots: tuple[CellSnapshot, ...]
    dropped_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_SNAPSHOT_JOURNAL_READER_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.dropped_count == 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "attempted_lines": self.attempted_lines,
            "dropped_count": self.dropped_count,
            "errors": list(self.errors),
            "next_offset": self.next_offset,
            "path": self.path,
            "schema": self.schema,
            "snapshot_count": len(self.snapshots),
            "start_offset": self.start_offset,
        }


def iter_cell_snapshot_jsonl(
    path: Path,
    *,
    strict: bool = False,
) -> Iterator[CellSnapshot]:
    """Replay a complete cell snapshot journal.

    In best-effort mode invalid lines are skipped. In strict mode the first
    invalid line raises the parsing error.
    """

    if not path.exists():
        if strict:
            raise FileNotFoundError(path)
        return

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield CellSnapshot.from_json_line(stripped)
            except Exception:
                if strict:
                    raise
                continue


def read_cell_snapshot_jsonl(
    path: Path,
    *,
    strict: bool = False,
    limit: int | None = None,
) -> CellSnapshotJournalReadResult:
    """Replay a journal into a read result.

    The result is suitable for offline analysis and for desktop visualization
    startup before switching to non-blocking tail reads.
    """

    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0")

    snapshots: list[CellSnapshot] = []
    errors: list[str] = []
    attempted = 0
    dropped = 0

    try:
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if limit is not None and len(snapshots) >= limit:
                    break

                stripped = line.strip()
                if not stripped:
                    continue

                attempted += 1
                try:
                    snapshots.append(CellSnapshot.from_json_line(stripped))
                except Exception as exc:
                    dropped += 1
                    message = f"line {line_number}: {type(exc).__name__}: {exc}"
                    if strict:
                        raise ValueError(message) from exc
                    errors.append(message)

    except Exception as exc:
        if strict:
            raise
        errors.append(f"{type(exc).__name__}: {exc}")

    return CellSnapshotJournalReadResult(
        path=str(path),
        attempted_lines=attempted,
        snapshots=tuple(snapshots),
        dropped_count=dropped,
        errors=tuple(errors),
    )


def tail_cell_snapshot_jsonl(
    path: Path,
    *,
    offset: int = 0,
    strict: bool = False,
    max_lines: int | None = None,
) -> CellSnapshotJournalTailResult:
    """Read new complete lines from a journal starting at a byte offset.

    This function is intentionally non-blocking. A live viewer calls it
    repeatedly. Live mode is therefore replay that has caught up with the end of
    the file.
    """

    if offset < 0:
        raise ValueError("offset must be >= 0")
    if max_lines is not None and max_lines < 0:
        raise ValueError("max_lines must be >= 0")

    snapshots: list[CellSnapshot] = []
    errors: list[str] = []
    attempted = 0
    dropped = 0
    next_offset = offset

    try:
        if not path.exists():
            raise FileNotFoundError(path)

        with path.open("r", encoding="utf-8") as handle:
            handle.seek(offset)

            while max_lines is None or attempted < max_lines:
                line_start = handle.tell()
                line = handle.readline()
                if line == "":
                    next_offset = handle.tell()
                    break

                if not line.endswith("\n"):
                    next_offset = line_start
                    break

                next_offset = handle.tell()
                stripped = line.strip()
                if not stripped:
                    continue

                attempted += 1
                try:
                    snapshots.append(CellSnapshot.from_json_line(stripped))
                except Exception as exc:
                    dropped += 1
                    message = f"offset {line_start}: {type(exc).__name__}: {exc}"
                    if strict:
                        raise ValueError(message) from exc
                    errors.append(message)

    except Exception as exc:
        if strict:
            raise
        errors.append(f"{type(exc).__name__}: {exc}")

    return CellSnapshotJournalTailResult(
        path=str(path),
        start_offset=offset,
        next_offset=next_offset,
        attempted_lines=attempted,
        snapshots=tuple(snapshots),
        dropped_count=dropped,
        errors=tuple(errors),
    )
