# 0046 — Part 9.2 Cell Observation Event Adapter

This patch prepares the handoff from synthetic data to real recorded observation data.

## Apply

```bash
python apply_patch_queue.py --patch 0046-part9_2_cell_observation_event_adapter --dry-run
python apply_patch_queue.py --patch 0046-part9_2_cell_observation_event_adapter --commit --push
```

## Scope

- Add `missipy.cell_observation_event.v1`.
- Convert recorded observation events to `missipy.cell.v1`.
- Add a JSONL conversion tool.
- Add tests and docs.

## Out of scope

- No live bus subscription.
- No recorder core mutation.
- No Scheduler path.
- No VisPy change.
- No mobile SSE.
