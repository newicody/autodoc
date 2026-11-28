# Changelog — 0226 snapshot/audit/replay supervision contract

## Added

- Documented the optional-output boundary for snapshot, audit journal, replay, and future VisPy views.
- Explicitly preserved `EventBus -> PassiveSupervisorSink -> CellularState` as the canonical live path.
- Added a code rule preventing `events.jsonl`, `snapshot.json`, status files, or VisPy from becoming mandatory runtime inputs.
- Added DOT architecture for the optional outputs and forbidden reverse-control paths.

## Not changed

- No runtime code.
- No new EventBus.
- No Scheduler changes.
- No `Scheduler.run()` usage.
- No proxy/SHM/policy control.
- No SQL/Qdrant/GitHub mutation.
- No VisPy dependency.
