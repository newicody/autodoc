# 0184 route request to command dry-run plan rule

0184 builds a reviewable request-to-command plan only.

Rules:

- Read scheduler.route_requests.jsonl from 0179.
- Build only route_request_to_command_dry_run_plan.jsonl.
- Normalize typed refs for the existing command builder.
- Target build_single_frame_route_command as the later builder surface.
- Do not import runtime handler modules.
- Do not call build_single_frame_route_command.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
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
