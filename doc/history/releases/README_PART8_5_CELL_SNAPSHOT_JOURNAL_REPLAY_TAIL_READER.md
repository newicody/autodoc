# Part 8.5 — Cell Snapshot Journal Replay/Tail Reader

Part 8.5 adds replay and non-blocking tail readers for the cell snapshot JSONL
journal.

## Added

- `src/context/cell_snapshot_journal_reader.py`
- Replay reader.
- Non-blocking tail reader.
- Best-effort and strict modes.
- Bounded replay/tail support.
- Tests and contract documentation.

## Not added

- No EventBus consumer.
- No recorder stream integration.
- No VisPy.
- No mobile SSE.
- No optimization loop.
