# Changelog — 0182 Route handler dry-run handoff plan

## Added

- Dry-run handoff planner from `scheduler.route_requests.jsonl` to optional
  `route_handler_dry_run_plan.jsonl`.
- AST signature extraction for `handle_scheduler_route_request`.
- Tests/rules locking that no handler import, handler call, Scheduler
  modification, EventBus instantiation, frame write, GitHub API, network,
  conversion, inference, SQL, Qdrant, or VisPy write is introduced.

## Not changed

- No new runtime handler.
- No Scheduler.run modification.
- No route handler execution.
- No ControlProxy/RouteProxy frame write.
