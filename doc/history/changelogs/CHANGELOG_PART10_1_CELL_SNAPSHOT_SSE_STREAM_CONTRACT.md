# Changelog — Part 10.1 Cell Snapshot SSE Stream Contract

## Added

- `CELL_SNAPSHOT_SSE_SCHEMA`
- `CellSnapshotSseEvent`
- `format_sse_event`
- `snapshot_to_sse_event`
- `snapshots_to_sse_text`
- `cell_journal_to_sse_text`
- `tools/cell_snapshot_sse_dry_run.py`

## Behavior

A `missipy.cell.v1` journal can now be converted into read-only SSE text without
opening a server socket.
