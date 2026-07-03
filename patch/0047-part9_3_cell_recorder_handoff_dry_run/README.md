# 0047 — Part 9.3 Cell Recorder Handoff Dry-Run

This patch validates recorded observation data to cell snapshot journal compatibility.

## Apply

```bash
python apply_patch_queue.py --patch 0047-part9_3_cell_recorder_handoff_dry_run --dry-run
python apply_patch_queue.py --patch 0047-part9_3_cell_recorder_handoff_dry_run --commit --push
```

## Scope

- Add dry-run handoff module.
- Convert recorded observation JSONL to cell snapshot journal.
- Replay-check the produced journal.
- Add CLI, tests, and docs.

## Out of scope

- No live subscription.
- No recorder core mutation.
- No Scheduler path.
- No VisPy change.
- No mobile SSE.
