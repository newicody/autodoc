# Cell Snapshot Journal Reader Contract v1

```text
schema: missipy.cell_snapshot_journal_reader.v1
line schema: missipy.cell.v1
```

The cell snapshot journal reader is the replay/tail read boundary for the
cell-population visualization track.

It is observation-only.

## Purpose

```text
JSONL cell snapshot journal
→ replay reader
→ tail reader
→ VisPy, future mobile view, analysis scripts
```

The reader does not schedule, cancel, mutate, or decide work.

## Replay

Replay reads the journal from the beginning and returns ordered
`missipy.cell.v1` snapshots.

Best-effort mode skips invalid lines and reports errors. Strict mode raises on
the first invalid line.

## Tail

Tail reads new complete lines from a byte offset and returns the next offset.

Tail is non-blocking. It never waits for future data.

Live mode is replay that has caught up to the end of the journal and then calls
tail repeatedly.

## Bounded work

Tail supports a maximum line count so that visualization work can be bounded.

Replay supports a limit for startup or diagnostic uses.

## Boundary rule

The reader must not import VisPy, server code, Scheduler code, EventBus code, or
network clients.

It reads files only. It does not emit commands.
