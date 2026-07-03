# Changelog — Part 9.2 Cell Observation Event Adapter

## Added

- `CELL_OBSERVATION_EVENT_SCHEMA`
- `CellObservationEvent`
- `derive_cell_snapshots_from_observation_events`
- `tools/convert_cell_observation_events.py`

## Behavior

Recorded observation events can now be converted into the same
`missipy.cell.v1` JSONL journal consumed by replay/tail and visualization.
