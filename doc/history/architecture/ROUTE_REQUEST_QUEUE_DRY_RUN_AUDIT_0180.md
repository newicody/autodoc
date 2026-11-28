# 0180 — Route request queue dry-run audit

## Decision

0180 is a dry-run audit, not route execution.

The input is scheduler.route_requests.jsonl.
The output is a readiness report.

It validates queued items through SchedulerRouteRequest.from_mapping.
It does not call handle_scheduler_route_request.
It does not modify Scheduler.run().
It does not write ControlProxy or RouteProxy frames.

## Why this exists

0179 materializes authorized SchedulerRouteRequest mappings into a local handoff
queue.

0180 checks that this queue is structurally ready for a later handler handoff,
without executing the handler and without writing runtime frames.

This gives a safe boundary before any future patch touches route execution:

```text
scheduler.route_requests.jsonl
-> dry-run validation/audit
-> readiness report
```

## Boundary

0180:

- reads `scheduler.route_requests.jsonl`,
- validates every row through `SchedulerRouteRequest.from_mapping(...)`,
- verifies each row is authorized,
- reports ready/blocked counts,
- checks that expected handler surface files exist.

0180 does not:

- call handle_scheduler_route_request,
- instantiate Scheduler,
- modify Scheduler.run(),
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
The dry-run report does not grant execution.
