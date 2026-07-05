# 0095 — locked route generation materializer

0095 composes the 0094 route generation lock with the 0091-r2 generation table
materializer. The operational path is intentionally small:

```text
with acquire_route_generation_lock(controlfs_root, route_id):
    load -> verify -> materialize -> persist
```

The goal is to protect the ControlProxy-side table:

```text
route_id -> current_generation
```

This is the safe step before concurrent g2/g3 updates. The table remains
incremented only when a new route generation is materialized. Normal Scheduler
handshakes, route writes, route reads and notifier wakeups do not allocate a
new generation.

## Boundary

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No live mmap resize.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- Not /dev/shm-only; the runtime root remains injectable and can still be file-backed.
- standard library only.

0095 does not replace policy/zone/scope authorization. It only serializes the
local ControlFS mutation once an already-authorized `RoutePrepareDecision`
reaches the generation materializer.

## code_rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0095 adds an importable IO-boundary composition around an existing lock and materializer; no new programming rule is needed.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
