# Cell Lens Phase 9 Handoff

This handoff document defines what the next phase may build.

## Current source of truth

The source of truth is still the local machine and the local repository.

For visualization, the source of truth is the local `missipy.cell.v1` JSONL
journal.

## Stable contracts

```text
missipy.cell.v1
missipy.cell_snapshot_journal.v1
missipy.cell_snapshot_journal_reader.v1
missipy.cell_synthetic_population.v1
missipy.cell_observation_event.v1
missipy.cell_recorder_handoff_dry_run.v1
```

## Phase 10 allowed next step

Phase 10 may add:

```text
local server
SSE stream
browser view
Canvas or WebGL rendering
```

The stream must read the same journal.

## Phase 10 forbidden path

Phase 10 must not add:

```text
remote mutation
mobile source of truth
browser command channel
EventBus command channel
optimization loop
autonomous agent
```

## Rule for any future action

Any future action from a UI must leave the UI as a typed command submitted to
the Scheduler.

It must not travel through the EventBus, journal, replay reader, SSE stream, or
visualization state.
