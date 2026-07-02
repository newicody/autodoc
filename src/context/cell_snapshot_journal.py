from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from context.cell_snapshot import CellSnapshot


CELL_SNAPSHOT_JOURNAL_SCHEMA = "missipy.cell_snapshot_journal.v1"


@dataclass(frozen=True, slots=True)
class CellSnapshotJournalWriteResult:
    """Result of a best-effort cell snapshot journal write."""

    path: str
    attempted_count: int
    written_count: int
    dropped_count: int
    errors: tuple[str, ...] = ()
    schema: str = CELL_SNAPSHOT_JOURNAL_SCHEMA

    @property
    def ok(self) -> bool:
        return not self.errors and self.written_count == self.attempted_count

    def to_json_dict(self) -> dict[str, object]:
        return {
            "attempted_count": self.attempted_count,
            "dropped_count": self.dropped_count,
            "errors": list(self.errors),
            "path": self.path,
            "schema": self.schema,
            "written_count": self.written_count,
        }


@dataclass(frozen=True, slots=True)
class CellSnapshotJournalWriter:
    """Append-only JSONL writer for observation snapshots.

    This writer is a boundary utility. It materializes immutable snapshots for
    visualization and analysis consumers, but it is not part of the decision
    path and does not emit commands.
    """

    path: Path
    strict: bool = False

    def append(self, snapshot: CellSnapshot) -> CellSnapshotJournalWriteResult:
        return self.append_many((snapshot,))

    def append_many(self, snapshots: Iterable[CellSnapshot]) -> CellSnapshotJournalWriteResult:
        materialized = tuple(snapshots)
        attempted = len(materialized)

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                written = 0
                errors: list[str] = []
                for index, snapshot in enumerate(materialized):
                    if not isinstance(snapshot, CellSnapshot):
                        message = f"item {index} is not a CellSnapshot"
                        if self.strict:
                            raise TypeError(message)
                        errors.append(message)
                        continue
                    handle.write(snapshot.to_json_line())
                    written += 1

            return CellSnapshotJournalWriteResult(
                path=str(self.path),
                attempted_count=attempted,
                written_count=written,
                dropped_count=attempted - written,
                errors=tuple(errors),
            )
        except Exception as exc:
            if self.strict:
                raise
            return CellSnapshotJournalWriteResult(
                path=str(self.path),
                attempted_count=attempted,
                written_count=0,
                dropped_count=attempted,
                errors=(f"{type(exc).__name__}: {exc}",),
            )


def write_cell_snapshots_jsonl(
    path: Path,
    snapshots: Iterable[CellSnapshot],
    *,
    strict: bool = False,
) -> CellSnapshotJournalWriteResult:
    return CellSnapshotJournalWriter(path=path, strict=strict).append_many(snapshots)
