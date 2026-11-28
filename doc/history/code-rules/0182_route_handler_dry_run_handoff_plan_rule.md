# 0182 route handler dry-run handoff plan rule

0182 builds a reviewable handoff plan only.

Rules:

- Read scheduler.route_requests.jsonl from 0179.
- Build only route_handler_dry_run_plan.jsonl.
- Inspect the handler file as AST/text only.
- Do not call handle_scheduler_route_request.
- Do not import runtime handler modules.
- Do not add a new runtime handler.
- Do not modify Scheduler.run.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not write ControlProxy or RouteProxy frames.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
