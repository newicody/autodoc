# 0186 — Isolated handler execution plan

## Decision

0186 plans isolated handler execution, but does not execute it.

The input is scheduler_route_handler_command_smoke.jsonl.
The output is isolated_handler_execution_plan.jsonl.

It resolves RouteProxyRuntimePolicy by AST only.
It does not call prepare_route_proxy_runtime.
It does not call handle_scheduler_route_command.

A future patch may execute the handler only inside the isolated runtime root.

## Why this exists

0185 proves that an authorized request can be transformed into a real
`SchedulerRouteHandlerCommand`.

Calling `handle_scheduler_route_command` would invoke RouteProxyRuntime IO. Before
that is allowed, the runtime root must be explicit, isolated, and reviewable.

0186 reads the existing `route_proxy_runtime_minimal.py` surface as text/AST and
detects how an isolated `RouteProxyRuntimePolicy` could be constructed later.

## Boundary

0186:

- reads `scheduler_route_handler_command_smoke.jsonl`,
- reads `src/runtime/route_proxy_runtime_minimal.py` as text/AST,
- resolves `RouteProxyRuntimePolicy`,
- resolves `prepare_route_proxy_runtime`,
- selects a candidate isolated root field,
- writes optional `isolated_handler_execution_plan.jsonl`.

0186 does not:

- import runtime handler modules,
- import route_proxy_runtime_minimal,
- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- call prepare_route_proxy_runtime,
- request writer permits,
- write RouteProxy frames,
- write ControlProxy frames,
- add a new runtime handler,
- instantiate Scheduler,
- modify Scheduler.run,
- instantiate EventBus,
- create a parallel bus,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
The isolated plan is not permission to execute outside the explicit runtime root.
