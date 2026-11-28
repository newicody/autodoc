# Changelog — Part 8.5 Cell Snapshot Journal Replay/Tail Reader

## Added

- `CELL_SNAPSHOT_JOURNAL_READER_SCHEMA`
- `CellSnapshotJournalReadResult`
- `CellSnapshotJournalTailResult`
- `iter_cell_snapshot_jsonl`
- `read_cell_snapshot_jsonl`
- `tail_cell_snapshot_jsonl`

## Behavior

Replay reads historical JSONL snapshots.

Tail reads new complete lines from a byte offset without blocking.

## Not changed

- No Scheduler path.
- No EventBus subscription.
- No recorder core modification.
- No renderer dependency.
- No network dependency.
