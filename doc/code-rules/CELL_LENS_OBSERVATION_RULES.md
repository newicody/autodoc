# Cell Lens Observation Rules

These rules extend the project code rules for the cell-population visualization
track.

## Rule 1 — Visualization is observation only

The cell lens observes the system through the observation path.

```text
EventBus / recorder / replay / journal
```

It must not command the system.

## Rule 2 — EventBus is not a command channel

The EventBus may carry observation events. It must not be used for visualizer
actions or system commands.

Any future action must use:

```text
typed command → Scheduler
```

## Rule 3 — Snapshot contracts are versioned

The first cell snapshot schema is:

```text
missipy.cell.v1
```

Future enrichment requires a new schema version. Existing fields are not
silently repurposed.

## Rule 4 — Impurity is confined

Disk writes for the cell journal are recorder-boundary effects. Graphics imports
are visualization-boundary effects.

Kernel, Scheduler, EventBus core, contracts, and replay core must not import
VisPy.

## Rule 5 — Observation is best-effort

Visualization and snapshot journaling must not be required for deterministic
execution.

Under load, observation data may be dropped, sampled, or aggregated.

## Rule 6 — Health uses expected lifetime

Cell health is measured against expected lifecycle for the source class, not by
raw speed.

A slow LLM step may be healthy. A short task that stalls may be unhealthy.

## Rule 7 — Mobile is a window

The mobile view belongs in the local server phase. It receives the same journal
through local SSE and remains read-only.

The phone is not a source of truth.

## Rule 8 — Optimization loop is out of scope

A real-time optimization loop is not part of the current roadmap.

When it exists later, it must observe via journal/replay and act only through
typed Scheduler commands.
