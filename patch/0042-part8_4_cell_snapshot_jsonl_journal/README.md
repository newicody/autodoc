# 0042 — Part 8.4 Cell Snapshot JSONL Journal

This patch adds the append-only JSONL writer for `missipy.cell.v1` snapshots.

## Apply

```bash
python apply_patch_queue.py --patch 0042-part8_4_cell_snapshot_jsonl_journal --dry-run
python apply_patch_queue.py --patch 0042-part8_4_cell_snapshot_jsonl_journal --commit --push
```

## Scope

- Add `CellSnapshotJournalWriter`.
- Add best-effort write result.
- Add helper `write_cell_snapshots_jsonl`.
- Add tests and documentation.

## Out of scope

- No real EventBus consumer.
- No recorder stream integration.
- No replay/tail reader.
- No VisPy.
- No mobile SSE.
- No optimization loop.
