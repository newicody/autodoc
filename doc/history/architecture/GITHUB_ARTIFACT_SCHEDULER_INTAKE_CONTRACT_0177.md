# 0177 — GitHub artifact scheduler intake contract

## Decision

0177 is a scheduler intake contract, not a Scheduler implementation.

It reuses scheduler_route_request_mapping from the existing scheduler route
adapter. It does not call handle_scheduler_route_request, does not modify
Scheduler.run(), does not instantiate Scheduler, and does not bypass
Scheduler/policy/zone.

A candidate is not authorized work. A SchedulerRouteRequest is emitted only with
an explicit policy_decision_id.

## Why this exists

0176 turns GitHub artifact/server dataset outcomes into existing bus observation
facts.

0177 prepares the next boundary: a local scheduler-addressable candidate that
can later become an authorized SchedulerRouteRequest, but only after policy has
decided and provided a policy_decision_id.

## Boundary

The intake contract:

- builds an unauthorized scheduler intake candidate from dataset/bus observation
  metadata,
- optionally builds an authorized SchedulerRouteRequest mapping through
  `scheduler_route_request_mapping(...)`,
- requires explicit `policy_decision_id` for authorized route requests,
- does not call the route handler or handshake,
- does not write frames,
- does not publish bus facts,
- does not execute Scheduler,
- does not call GitHub,
- does not use network,
- does not run conversion,
- does not run inference.

## Authority

Scheduler/policy/zone remain the authority.

The contract only prepares data at the boundary. It does not decide security,
priority policy, route eligibility, or execution.


## Exact rule-test lock phrases — 0177

It does not modify Scheduler.run().

Additional exact locks:

A SchedulerRouteRequest is emitted only with an explicit policy_decision_id.
