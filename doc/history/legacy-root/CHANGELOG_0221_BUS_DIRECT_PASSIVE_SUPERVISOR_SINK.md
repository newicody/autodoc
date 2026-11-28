# Changelog 0221 - Bus-Direct Passive Supervisor Sink

## Added

- Extended `src/context/passive_bus_supervisor_cellular_snapshot.py` with
  `PassiveSupervisorSink`.
- Added an in-memory EventBus downstream sink that accepts canonical scheduler,
  proxy, SHM, policy, GitHub, SQL, Qdrant, rehydrate, and pushback events.
- Added optional audit JSONL output for replay/debug only.
- Added optional snapshot writing from the sink.
- Added tests proving Scheduler is represented as an upstream EventBus emitter,
  while the supervisor stays downstream-only.

## Changed

- Updated `tools/run_passive_bus_supervisor_cellular_snapshot_0220.py` so JSONL
  input is optional replay/test input, not the mandatory runtime path.
- Added `--event-json` for fileless smoke tests of canonical EventBus events.
- Kept `--events-jsonl` backward compatible for replay and the 0220 test.

## Boundary

- No Scheduler.run call.
- No scheduler dispatch.
- No new bus implementation.
- No proxy control.
- No raw SHM/mmap read.
- No policy decision.
- No GitHub mutation.
- No SQL/Qdrant writes.
- No VisPy dependency.
- No non-stdlib dependency.
