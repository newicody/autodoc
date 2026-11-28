# 0185 scheduler route handler command-builder smoke rule

0185 verifies the existing command builder without executing the route handler.

Rules:

- Read route_request_to_command_dry_run_plan.jsonl from 0184.
- Call only build_single_frame_route_command.
- Write only scheduler_route_handler_command_smoke.jsonl.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not prepare RouteProxyRuntime.
- Do not request writer permits.
- Do not write ControlProxy or RouteProxy frames.
- Do not add a new runtime handler.
- Do not modify Scheduler.run.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not create a parallel bus.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
