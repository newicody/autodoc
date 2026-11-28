# Route generation lock — 0094

Status: implementation patch.

0094 adds a small inter-process lock for the ControlProxy generation table.
The target is the generation allocation critical section introduced by 0091-r2:

```text
route_id -> current_generation
```

The lock path is a ControlFS sidecar:

```text
active/routes/<route_id>/generation.lock
```

The lock exists so that two local ControlProxy actors cannot allocate the same
`g2/g3` route generation concurrently. The counter still increments in the
caller, and it should increment only when a new route generation is
materialized. The lock itself never allocates a generation and never resizes a
route.

## Operational path

```text
with acquire_route_generation_lock(controlfs_root, route_id):
    load active/routes/<route_id>/generation_state.json
    verify next_generation
    create routes/<route_id>@gN/ring.bin
    persist generation_state.json
```

0094 intentionally does not modify the 0091-r2 materializer yet. It provides the
importable primitive that the next integration patch can wrap around
materialize_route_generation_candidate(). This keeps the patch small and avoids
changing Scheduler, Dispatcher, queue or component contracts.

## Implementation

The implementation uses `fcntl.flock` from the Python standard library. It is a
local inter-process lock for the developer/runtime host. It is not a distributed
cluster lock and it is not a NetworkBridge or HardwareBridge primitive.

The lock file is deliberately file-backed ControlFS coordination. It is not
/dev/shm-only; a future runtime root may point ControlFS or route storage to
/dev/shm without changing the lock contract.

## Boundaries

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No live mmap resize.
- No route generation allocation by the lock itself.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- standard library only.

## code_rule alignment

code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0094 adds an importable local inter-process lock at the
ControlProxy/ControlFS IO boundary. It does not add a CLI, daemon, watcher,
network path, backend, Scheduler modification, Qdrant, LLM, or OpenVINO path.
