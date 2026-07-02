# 0043 — Part 8.5 Cell Snapshot Journal Replay/Tail Reader

This patch adds replay and non-blocking tail readers for the cell snapshot JSONL journal.

## Apply

```bash
python apply_patch_queue.py --patch 0043-part8_5_cell_snapshot_journal_replay_tail_reader --dry-run
python apply_patch_queue.py --patch 0043-part8_5_cell_snapshot_journal_replay_tail_reader --commit --push
```

## Scope

- Add replay reader.
- Add non-blocking tail reader.
- Add best-effort and strict modes.
- Add bounded replay/tail support.
- Add tests and documentation.

## Out of scope

- No real EventBus consumer.
- No recorder stream integration.
- No VisPy.
- No mobile SSE.
- No optimization loop.
