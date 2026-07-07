# 0182 — Route handler dry-run handoff plan

## Decision

0182 builds a dry-run handoff plan, not a handler call.

The input is scheduler.route_requests.jsonl.
The output is route_handler_dry_run_plan.jsonl.

It reads the handler file as AST only.
It does not import the handler module.
It does not call handle_scheduler_route_request.

A future patch may consume the plan only after review.

## Why this exists

0179 writes authorized SchedulerRouteRequest entries.
0180 validates the route request queue.
0181 audits handler surface files.

0182 connects those audit results into a reviewable dry-run handoff plan without
executing the handler. This gives a concrete staging artifact before any future
route handler call is allowed.

## Boundary

0182:

- reads `scheduler.route_requests.jsonl`,
- validates queued entries through the existing queue reader,
- reads `src/runtime/scheduler_route_handler_minimal.py` as text/AST,
- extracts the `handle_scheduler_route_request` signature,
- writes optional `route_handler_dry_run_plan.jsonl`.

0182 does not:

- import runtime handler modules,
- call handle_scheduler_route_request,
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
The handoff plan is not permission to execute.
