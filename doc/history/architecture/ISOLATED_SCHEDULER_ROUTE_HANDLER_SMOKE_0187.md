# 0187 — Isolated Scheduler route handler smoke

## Decision

0187 executes the existing handler only inside an isolated runtime root.

The input is isolated_handler_execution_plan.jsonl.
The output is isolated_scheduler_route_handler_smoke.jsonl.

It may call handle_scheduler_route_command.
It must verify frame paths remain inside isolated_runtime_root.
It must not modify Scheduler.run.

This is the first RouteProxy frame write smoke.

## Why this exists

0186 proved that an isolated `RouteProxyRuntimePolicy` can be planned with an
explicit `route_root`.

0187 performs the smallest real handler smoke:

```text
SchedulerRouteHandlerCommand
-> handle_scheduler_route_command
-> RouteProxyRuntimePolicy(route_root=<isolated_runtime_root>)
-> isolated RouteProxy frame write
```

The smoke is intentionally scoped to a temporary/test runtime root and does not
touch Scheduler.run, EventBus, ControlProxy, GitHub, SQL, Qdrant, inference, or
VisPy.

## Boundary

0187:

- reads `isolated_handler_execution_plan.jsonl`,
- rebuilds the command through `build_single_frame_route_command`,
- constructs `RouteProxyRuntimePolicy` rooted in `isolated_runtime_root`,
- calls `handle_scheduler_route_command`,
- verifies written frame paths remain under `isolated_runtime_root`,
- writes optional `isolated_scheduler_route_handler_smoke.jsonl`.

0187 does not:

- modify Scheduler.run,
- instantiate Scheduler,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
0187 proves isolated handler IO only. It does not enable production route writes.
