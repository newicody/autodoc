# Changelog — 0180 Route request queue dry-run audit

## Added

- Dry-run audit for `scheduler.route_requests.jsonl`.
- Validation through `SchedulerRouteRequest.from_mapping`.
- Readiness report with item counts, ready/blocked counts, and expected handler
  surface presence.
- CLI for local dry-run queue audit.
- Tests/rules locking that no route execution, Scheduler modification, EventBus
  instantiation, frame write, GitHub API, network, conversion, inference, SQL,
  Qdrant, or VisPy write is introduced.

## Not changed

- No Scheduler.run modification.
- No route handler call.
- No ControlProxy/RouteProxy frame write.
