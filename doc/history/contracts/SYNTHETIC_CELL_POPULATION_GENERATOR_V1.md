# Synthetic Cell Population Generator v1

```text
schema: missipy.cell_synthetic_population.v1
output line schema: missipy.cell.v1
```

The synthetic cell population generator creates deterministic observation data
for the cell lens before the real EventBus/recorder consumer exists.

It is replaceable.

The faux flux and the true bus path must produce the same missipy.cell.v1
journal so the visualizer does not need to be rewritten.

## Purpose

```text
synthetic generator
→ missipy.cell.v1 snapshots
→ JSONL journal
→ replay/tail reader
→ future VisPy viewer
```

## Boundary rule

The generator does not subscribe to EventBus, does not call Scheduler, does not
emit commands, and does not import rendering code.

It is a development and test data source for the observation path.

## Determinism

The generator uses an explicit seed and a fixed base timestamp by default.

The same configuration produces the same snapshots.

## Source classes

Default profiles include:

```text
scheduler.short_task
llm.answer
ingest.batch
recorder.write
```

These profiles have different expected lifetimes so future health mapping can
test that slow is not always unhealthy.

## Replacement rule

When the real EventBus/recorder consumer is ready, the synthetic generator is
removed from the live chain. It may remain as a test fixture and demo source.

The visualizer must continue to read the same journal contract.
