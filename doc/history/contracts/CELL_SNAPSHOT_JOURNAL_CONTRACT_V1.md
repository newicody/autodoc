# Cell Snapshot JSONL Journal Contract v1

```text
schema: missipy.cell_snapshot_journal.v1
line schema: missipy.cell.v1
```

The cell snapshot journal is the first materialized observation boundary for
the cell-population visualization track.

It is best-effort and append-only.

## Purpose

```text
EventBus / recorder / replay
→ cell snapshot journal
→ VisPy, future mobile view, analysis scripts
```

The journal is not a command path. It does not schedule, cancel, mutate, or
decide work.

## File format

The journal is JSONL.

Each line is a serialized `missipy.cell.v1` snapshot.

```json
{"schema":"missipy.cell.v1","cell_id":"..."}
```

The file-level writer result uses:

```text
missipy.cell_snapshot_journal.v1
```

## Boundary rule

The writer is a recorder-boundary utility. It may perform disk I/O.

It must not block the Scheduler. It must not be required for deterministic
execution. It must not emit commands.

Under load or failure, observation data may be dropped, sampled, or aggregated
by later implementations.

## Versioning rule

Changing the line schema requires a new `missipy.cell.*` version.

Changing journal semantics requires a new `missipy.cell_snapshot_journal.*`
version.

## Current implementation

Part 8.4 only adds the JSONL writer.

It does not yet connect to the real EventBus or recorder stream. The real
consumer is introduced in a later patch using this same contract.
