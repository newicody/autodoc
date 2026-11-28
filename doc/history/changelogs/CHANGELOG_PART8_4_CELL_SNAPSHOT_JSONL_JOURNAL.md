# Changelog — Part 8.4 Cell Snapshot JSONL Journal

## Added

- `CELL_SNAPSHOT_JOURNAL_SCHEMA`
- `CellSnapshotJournalWriteResult`
- `CellSnapshotJournalWriter`
- `write_cell_snapshots_jsonl`

## Behavior

The writer appends serialized `missipy.cell.v1` snapshots to a JSONL file.
Writes are best-effort by default and strict only when explicitly requested.

## Not changed

- No Scheduler path.
- No EventBus subscription.
- No recorder core modification.
- No renderer dependency.
