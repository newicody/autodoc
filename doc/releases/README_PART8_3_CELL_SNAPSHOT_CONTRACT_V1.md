# Part 8.3 — Cell Snapshot Contract v1

Part 8.3 adds the runtime contract for cell-population observation snapshots.

## Added

- `src/context/cell_snapshot.py`
- Serialization/deserialization tests.
- Code-rule tests.
- Contract documentation.

## Scope

This patch defines `missipy.cell.v1` only.

It does not add:

```text
EventBus consumer
recorder writer
JSONL journal
VisPy viewer
mobile view
optimization loop
```
