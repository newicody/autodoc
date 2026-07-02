# Part 8.4 — Cell Snapshot JSONL Journal

Part 8.4 adds the append-only JSONL writer for `missipy.cell.v1` snapshots.

## Added

- `src/context/cell_snapshot_journal.py`
- Best-effort writer result.
- Append-only JSONL writer.
- Tests for append order, parent directory creation, invalid item handling, and write failure handling.
- Journal contract documentation.

## Not added

- No real EventBus consumer.
- No recorder stream integration.
- No replay/tail reader.
- No VisPy.
- No mobile view.
- No optimization loop.
