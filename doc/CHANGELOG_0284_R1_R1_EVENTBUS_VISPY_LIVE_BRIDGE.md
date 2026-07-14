# Changelog 0284-r1-r1 — EventBus VisPy live bridge

- Added an optional passive adapter from the existing EventBus to the existing `missipy.cell.v1` append-only journal.
- Reused `CellObservationEvent`, `CellSnapshotJournalWriter` and the existing VisPy tail reader.
- Enabled `--tail --interval-seconds 0.25` in the existing desktop VisPy launch profile.
- Added opt-in application composition through `MISSIPY_CELL_LENS_JOURNAL` without modifying the Scheduler or kernel launcher.
- Kept observer conversion and filesystem failures outside the command path.
- Documented that Copilot ProjectV2 visibility remains a separate controlled remote-publication concern.

```text
architecture_preserved: true
existing_eventbus_reused: true
existing_cell_contract_reused: true
existing_journal_reused: true
existing_vispy_tail_reused: true
new_bus_added: false
new_scheduler_added: false
scheduler_modified: false
eventbus_observation_only: true
sql_write_performed: false
qdrant_write_performed: false
github_api_added: false
external_dependencies_added: false
```
