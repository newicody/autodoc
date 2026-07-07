# Changelog — 0179 Authorized route request queue handoff

## Added

- Local JSONL handoff queue for authorized SchedulerRouteRequest mappings.
- Queue writer from context.bus via the 0178 reader.
- Validation of every queued item with SchedulerRouteRequest.from_mapping.
- CLI for writing scheduler.route_requests.jsonl.
- Tests and rules locking that no route execution, Scheduler modification,
  EventBus instantiation, frame write, GitHub API, network, conversion,
  inference, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No Scheduler.run modification.
- No route handler call.
- No ControlProxy/RouteProxy frame write.
