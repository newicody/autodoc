# 0179 — Authorized route request queue handoff

## Decision

0179 is a handoff queue, not route execution.

The handoff source is context.bus.jsonl. The output is
scheduler.route_requests.jsonl.

Every queued item is validated with SchedulerRouteRequest.from_mapping.
Only authorized SchedulerRouteRequest mappings are queued. An explicit
policy_decision_id is required.

handle_scheduler_route_request is not called.
Scheduler.run() is not modified.

## Why this exists

0176 writes GitHub artifact dataset observations to the existing bus files.
0178 reads context.bus.jsonl and builds scheduler intake plans.
0179 materializes the authorized result into a local handoff queue.

This gives a clear next boundary:

```text
context.bus.jsonl
-> 0178 reader
-> authorized SchedulerRouteRequest
-> scheduler.route_requests.jsonl
```

The queue is not execution. It is a staging/handoff file for a later patch that
can integrate with the existing route handler under Scheduler/policy/zone
authority.

## Boundary

0179:

- reads from `context.bus.jsonl` through the 0178 reader,
- requires explicit `policy_decision_id`,
- validates every item with `SchedulerRouteRequest.from_mapping(...)`,
- appends JSONL into `scheduler.route_requests.jsonl`,
- reports count and queue path.

0179 does not:

- instantiate Scheduler,
- modify Scheduler.run(),
- call handle_scheduler_route_request,
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
The queue contains authorized route request data, but it does not execute it.


## Exact rule-test lock phrases — 0179

The output is scheduler.route_requests.jsonl.
