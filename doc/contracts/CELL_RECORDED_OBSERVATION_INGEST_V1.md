# Cell Recorded Observation Ingest v1

```text
schema: missipy.cell_recorded_observation_ingest.v1
state schema: missipy.cell_recorded_observation_ingest_state.v1
input schema: missipy.cell_observation_event.v1
output schema: missipy.cell.v1
```

This contract ingests recorded observation events into the stable cell snapshot
journal.

It is observation-only.

It is not a command path.

## Purpose

```text
recorded observation JSONL
→ missipy.cell_observation_event.v1
→ missipy.cell.v1 journal
→ replay/tail
→ views
```

## Incremental state

The ingest keeps an offset state file.

```text
source_path
next_offset
```

A repeated run reads only lines appended after the previous offset.

## Boundary

The ingest reads local recorded observations, appends snapshots, and writes
offset state.

It does not render, stream, subscribe to a live source, call a remote API, or
dispatch actions.
