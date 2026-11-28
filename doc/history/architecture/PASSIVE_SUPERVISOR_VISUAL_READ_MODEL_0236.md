# Passive supervisor visual read-model — 0236

## Intent

This patch prepares the human visualization path without adding VisPy and without
changing runtime authority.

The canonical path remains:

```text
Scheduler / runtime surfaces / data surfaces
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
  -> snapshot
  -> visual read-model
  -> VisPy later
```

VisPy is not introduced by this patch.

## What is added

`src/context/passive_supervisor_visual_read_model.py` derives a stable
JSON-compatible read-model from an existing passive supervisor snapshot.

It produces:

```text
nodes
edges
zones
authority_boundary
source_snapshot counters
```



## Visual read path

```text
snapshot -> visual read-model
```

The visual read-model is a read-only transformation for human display.

## Canonical upstream path

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

The visual read-model is downstream of this path. It reads a snapshot or
snapshot-like mapping and never becomes part of the runtime authority path.

## Boundary

The read-model is downstream-only:

```text
no Scheduler.run()
no EventBus creation
no proxy control
no SHM mutation
no policy decision
no SQL write
no Qdrant write
no GitHub mutation
no non-stdlib dependency
```

The read-model observes movement through references and zones, but it does not
move data, routes, leases, or authority.
