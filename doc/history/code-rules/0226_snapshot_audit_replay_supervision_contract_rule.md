# Code rule — 0226 snapshot/audit/replay supervision boundary

Any work after 0226 touching passive supervision must preserve this boundary:

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

Snapshot, audit journal, replay files, and VisPy are optional downstream outputs or test harnesses. They are not mandatory runtime inputs.

Required constraints:

- Do not make `events.jsonl` mandatory for live supervision.
- Do not make `snapshot.json` the normal upstream source of truth.
- Do not add a status-file-first bridge for Scheduler, proxy, SHM, policy, GitHub, SQL, Qdrant, rehydration, or pushback.
- Do not place VisPy in the critical runtime path.
- Do not call or wrap `Scheduler.run()` from the passive supervisor.
- Do not let replay claim authority over runtime decisions.
- Keep audit/replay visibly optional and test/debug oriented.
- Keep the supervisor downstream-only.

Allowed:

- `PassiveSupervisorSink.snapshot()` for inspection.
- Optional `write_snapshot(path)`.
- Optional audit journal emitted after accepting a bus event.
- Replay harnesses for regression tests and debugging.
- Future VisPy views that read `snapshot()` or `snapshot.json` only.
