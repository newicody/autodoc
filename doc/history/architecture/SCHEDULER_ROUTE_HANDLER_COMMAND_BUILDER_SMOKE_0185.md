# 0185 — Scheduler route handler command-builder smoke

## Decision

0185 calls the existing command builder, not the route handler.

The input is route_request_to_command_dry_run_plan.jsonl.
The output is scheduler_route_handler_command_smoke.jsonl.

It may import build_single_frame_route_command.
It must not call handle_scheduler_route_command.
It must not prepare RouteProxyRuntime.

A future patch may execute the handler only after this smoke is reviewed.

## Why this exists

0184 builds reviewable keyword arguments for the existing
`build_single_frame_route_command` surface.

0185 is the first controlled import smoke. It verifies that those planned
keyword arguments can build a real `SchedulerRouteHandlerCommand` object using
the existing code.

This is still not route execution.

## Boundary

0185:

- reads `route_request_to_command_dry_run_plan.jsonl`,
- imports `SchedulerRouteHandlerCommand`,
- imports `build_single_frame_route_command`,
- calls only `build_single_frame_route_command`,
- writes optional `scheduler_route_handler_command_smoke.jsonl`.

0185 does not:

- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- prepare RouteProxyRuntime,
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
The smoke output proves command shape only. It does not grant route execution.
