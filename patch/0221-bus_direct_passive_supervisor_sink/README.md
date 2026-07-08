# 0221 - Bus-Direct Passive Supervisor Sink

This patch updates the existing passive bus supervisor introduced by 0220. It
does not introduce a new bus or a parallel bridge.

Canonical runtime path:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy
  -> EventBus
  -> PassiveSupervisorSink.accept(event)
  -> in-memory cellular state
  -> optional snapshot.json
  -> optional events.jsonl audit/replay
```

Requirements before applying:

- Patch `0220-passive_bus_supervisor_cellular_snapshot` is applied.
- Patch `0220-r1-passive_bus_supervisor_cli_import_path_fix` is applied.
- The full suite is green after 0220-r1.

Validation performed in sandbox on a skeleton repository with 0220 + 0220-r1:

- `git apply --check`: OK
- `git apply`: OK
- `python -m compileall -q src tests tools`: OK
- `python -m pytest -q tests/context tests/tools tests/rules`: 12 passed
- CLI smoke with `--event-json`: OK
- CLI replay with `--events-jsonl`: OK

Authority boundary:

- no `Scheduler.run`
- no scheduler dispatch
- no proxy control
- no raw SHM/mmap read
- no policy decision
- no SQL/Qdrant write
- no GitHub mutation
- no VisPy
- no non-stdlib dependency
