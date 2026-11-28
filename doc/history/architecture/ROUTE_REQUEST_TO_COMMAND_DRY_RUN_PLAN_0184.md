# 0184 — Route request to command dry-run plan

## Decision

0184 maps SchedulerRouteRequest data into command-builder kwargs.

The input is scheduler.route_requests.jsonl.
The output is route_request_to_command_dry_run_plan.jsonl.

It targets build_single_frame_route_command.
It does not call build_single_frame_route_command.
It does not call handle_scheduler_route_command.

A future patch may consume this plan only after review.

## Why this exists

0183 resolved the real handler split:

```text
SchedulerRouteRequest / handle_scheduler_route_request
```

is the request/adapter boundary, while:

```text
SchedulerRouteHandlerCommand / handle_scheduler_route_command
```

is the minimal command handler boundary.

0184 bridges these two concepts as a dry-run plan only. It converts authorized
route request metadata into typed refs and keyword arguments suitable for later
review against `build_single_frame_route_command`.

## Boundary

0184:

- reads `scheduler.route_requests.jsonl`,
- normalizes typed refs for the existing command builder,
- builds reviewable keyword arguments,
- optionally writes `route_request_to_command_dry_run_plan.jsonl`.

0184 does not:

- import runtime handler modules,
- call build_single_frame_route_command,
- call handle_scheduler_route_command,
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

## Ref normalization

0184 only plans typed refs:

```text
command_ref -> scheduler-command:<task_id>
route_ref   -> route:<route_id>
owner_ref   -> scheduler-command:<task_id>
context_ref -> ctx:<request_id>
```

It does not claim these refs are final business authority. Scheduler/policy/zone
remain authoritative.
