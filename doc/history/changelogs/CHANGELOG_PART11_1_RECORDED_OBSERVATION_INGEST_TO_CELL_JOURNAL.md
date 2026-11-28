# Changelog — Part 11.1 Recorded Observation Ingest to Cell Journal

## Added

- `CELL_RECORDED_OBSERVATION_INGEST_SCHEMA`
- `CELL_RECORDED_OBSERVATION_STATE_SCHEMA`
- `CellRecordedObservationIngestState`
- `CellRecordedObservationReadResult`
- `CellRecordedObservationIngestResult`
- `ingest_recorded_observation_events_to_cell_journal`
- `tools/ingest_recorded_observations_to_cell_journal.py`

## Behavior

A recorded observation JSONL file can now be incrementally ingested into a
`missipy.cell.v1` journal using an offset state file.
