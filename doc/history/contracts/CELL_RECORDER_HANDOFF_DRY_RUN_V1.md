# Cell Recorder Handoff Dry-Run v1

```text
schema: missipy.cell_recorder_handoff_dry_run.v1
input schema: missipy.cell_observation_event.v1
output schema: missipy.cell.v1
```

This dry-run validates the future handoff from recorded observation data to the
cell snapshot journal.

It has no live subscription.

It is not a command path.

## Purpose

```text
recorded observation JSONL
→ missipy.cell_observation_event.v1
→ missipy.cell.v1
→ JSONL journal
→ replay reader
```

The dry-run validates that recorded observations produce the same missipy.cell.v1 journal consumed by replay, analysis, and visualization.

## Boundary

The dry-run reads and writes local files only. It does not command, schedule,
subscribe, render, stream, or mutate the running system.

## Done criterion

```text
event_count == snapshot_count == replay_count
cell order is preserved
journal is replayable
errors are reported
```
