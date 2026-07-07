# Changelog — 0184 Route request to command dry-run plan

## Added

- Dry-run request-to-command planner for authorized SchedulerRouteRequest queue
  entries.
- Typed-ref normalization for later `build_single_frame_route_command` review.
- Optional `route_request_to_command_dry_run_plan.jsonl` output.
- Tests/rules locking that no handler import, builder call, handler call,
  Scheduler modification, EventBus instantiation, frame write, GitHub API,
  network, conversion, inference, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No command builder execution.
- No route handler execution.
- No ControlProxy/RouteProxy frame write.
