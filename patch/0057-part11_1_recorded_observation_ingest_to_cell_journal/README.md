# 0057 — Part 11.1 Recorded Observation Ingest to Cell Journal

This patch starts the post-UI handoff back to recorded observation production.

## Apply

```bash
python apply_patch_queue.py --patch 0057-part11_1_recorded_observation_ingest_to_cell_journal --dry-run
python apply_patch_queue.py --patch 0057-part11_1_recorded_observation_ingest_to_cell_journal --commit --push
```

## Scope

- Add incremental recorded observation ingest.
- Convert `missipy.cell_observation_event.v1` to `missipy.cell.v1`.
- Append to the cell journal.
- Persist offset state.
- Add CLI, tests, and docs.

## Out of scope

- No live subscription.
- No renderer.
- No server.
- No command channel.
- No optimization loop.
