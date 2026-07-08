# Patch 0222 - Scheduler EventBus Supervisor Source

This patch updates the existing passive bus supervisor surface from 0220/0221.
It standardizes how Scheduler upstream events are represented as canonical
EventBus supervision events and validates them through `PassiveSupervisorSink`.

It does not import Scheduler, call `Scheduler.run`, dispatch handlers, implement
an EventBus, control proxy/SHM/policy, or mutate SQL/Qdrant/GitHub.

Apply after:

- `0220-passive_bus_supervisor_cellular_snapshot`
- `0220-r1-passive_bus_supervisor_cli_import_path_fix`
- `0221-bus_direct_passive_supervisor_sink`

Validation target:

```bash
python apply_patch_queue.py --patch 0222-scheduler_eventbus_supervisor_source --dry-run --allow-dirty
python apply_patch_queue.py --patch 0222-scheduler_eventbus_supervisor_source --commit --push --allow-dirty
```
