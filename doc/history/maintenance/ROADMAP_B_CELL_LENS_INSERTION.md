# Roadmap B — Cell Lens Insertion

This document inserts the cell-population visualization track into Roadmap B.

The visualization is a lens, not a lever.

```text
observation path: EventBus / recorder / replay / journal
command path: typed command / Scheduler
```

The two paths must remain separate.

## Active placement

```text
Phase 8 — Local foundation / contracts / observability
  8.x Cell snapshot contract missipy.cell.v1
  8.x EventBus/recorder consumer to JSONL cell snapshot journal
  8.x Replay/tail reader contract for the cell journal

Phase 9 — Local replay / desktop visualization
  9.x Synthetic cell population generator
  9.x VisPy desktop viewer reading the journal
  9.x Health mapping by expected lifetime per task class
  9.x Switch synthetic source to real EventBus/recorder output

Phase 10 — Local server
  10.x SSE stream from the same journal
  10.x Mobile browser view as a window, not a source of truth

Out of scope
  X.x Real-time optimization loop
```

## Step 1 — Cell snapshot contract

Phase: 8.

Schema:

```text
missipy.cell.v1
```

Purpose:

```text
one immutable observation snapshot derived from task/component events
```

Minimal fields:

```text
schema
cell_id
source_task_id
source_component_id
source_class
score
age
cost
lifecycle_state
observed_at
```

Done when:

```text
- the schema is versioned as missipy.cell.v1
- snapshots are immutable value objects
- serialization/deserialization tests exist
- no VisPy dependency exists in the contract
- future enrichment requires missipy.cell.v2 or later
```

Do not:

```text
- do not encode commands in the snapshot
- do not make the snapshot mutable
- do not silently change missipy.cell.v1
- do not define the contract inside the visualizer
```

## Step 2 — EventBus/recorder to JSONL snapshot journal

Phase: 8.

Purpose:

```text
materialize observation snapshots through the existing recorder/replay path
```

Done when:

```text
- a consumer derives missipy.cell.v1 snapshots from observation events
- JSONL output is append-only and ordered enough for replay
- disk writes are best-effort and confined to the recorder boundary
- failure to write does not affect scheduling or decisions
- overload can drop or aggregate observation data
```

Do not:

```text
- do not write to the decision path
- do not block the Scheduler
- do not invent a second recorder
- do not use EventBus as a command channel
```

## Step 3 — VisPy desktop viewer

Phase: 9.

Purpose:

```text
read the cell journal and render a population of cells
```

The viewer can be developed against a synthetic generator before the real bus
consumer exists. The generator must write the same `missipy.cell.v1` journal.

Live mode is only replay that has caught up to the end of the file.

Done when:

```text
- replay mode reads historical JSONL
- tail mode reads the same JSONL format
- synthetic generator produces contract-compliant snapshots
- no command leaves VisPy
- health is based on deviation from expected lifetime by source class
```

Do not:

```text
- do not connect VisPy directly to the Scheduler
- do not make VisPy a source of truth
- do not make graphics imports part of the kernel
- do not judge health by raw shortness or slowness
```

## Step 4 — Synthetic source to real bus

Phase: late 9.

Purpose:

```text
replace synthetic journal production with real EventBus/recorder production
```

Done when:

```text
- the real journal uses the same missipy.cell.v1 schema
- VisPy runs without modification
- compatibility tests compare synthetic and real snapshots
- the recorder remains optional for deterministic decisions
```

Do not:

```text
- do not rewrite the viewer for the real bus
- do not change missipy.cell.v1 silently
- do not bypass the recorder
```

## Step 5 — Mobile view

Phase: 10.

Purpose:

```text
stream the same journal over local SSE to a phone browser
```

The phone is a window. The local machine remains the source of truth.

Done when:

```text
- local server streams journal snapshots over SSE
- browser renders a read-only Canvas/WebGL view
- reconnect is tolerated
- no command path is exposed by the mobile view
```

Do not:

```text
- do not port VisPy to mobile
- do not create a mobile app in this phase
- do not make the phone a source of truth
- do not expose remote mutation
```

## Step 6 — Real-time optimization loop

Status: out of scope.

It requires:

```text
- a real flow to optimize
- a defined fitness function
- complete ordered observation journal
- typed command contracts
- Scheduler command path
- simulation/replay guardrails
```

Do not design it now.
