# Changelog — Part 8.6 Synthetic Cell Population Generator

## Added

- `CELL_SYNTHETIC_POPULATION_SCHEMA`
- `SyntheticCellClassProfile`
- `SyntheticCellPopulationConfig`
- `SyntheticCellSeed`
- `build_synthetic_cell_seeds`
- `generate_synthetic_cell_snapshots`
- `tools/generate_synthetic_cell_journal.py`

## Behavior

The generator emits deterministic `missipy.cell.v1` snapshots suitable for
JSONL journaling and later visualization.

## Not changed

- No Scheduler path.
- No EventBus subscription.
- No recorder core modification.
- No renderer dependency.
- No network dependency.
