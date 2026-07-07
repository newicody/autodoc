# 0183 — Route handler surface resolver

## Decision

0183 resolves the real route handler surfaces, not guessed symbols.

The real minimal handler surface is handle_scheduler_route_command.
The adapter request surface is handle_scheduler_route_request.

0183 does not execute either surface.

A future patch must consume this resolver report before any handler call.

## Why this exists

0182 proved that `src/runtime/scheduler_route_handler_minimal.py` does not expose
`handle_scheduler_route_request`.

The repository already has a different, more precise surface:

```text
SchedulerRouteHandlerCommand
handle_scheduler_route_command(...)
handle_scheduler_route_command_with_readback(...)
build_single_frame_route_command(...)
```

The request-level adapter surface exists separately:

```text
SchedulerRouteRequest
handle_scheduler_route_request(...)
scheduler_route_request_mapping(...)
```

0183 records this split so future work reuses existing code instead of adding a
parallel handler.

## Boundary

0183:

- reads route-related files as text,
- parses AST,
- reports available surfaces and signatures,
- recommends the next existing surface to review.

0183 does not:

- import runtime handler modules,
- call handle_scheduler_route_request,
- call handle_scheduler_route_command,
- add a new runtime handler,
- instantiate Scheduler,
- modify Scheduler.run,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
The resolver report does not grant execution.
