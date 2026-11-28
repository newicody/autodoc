# 0183 route handler surface resolver rule

0183 resolves existing route handler surfaces before execution.

Rules:

- Resolve existing route handler surfaces before execution.
- Prefer handle_scheduler_route_command when available.
- Treat handle_scheduler_route_request as an adapter request surface.
- Do not add a new runtime handler in 0183.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_request.
- Do not call handle_scheduler_route_command.
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
