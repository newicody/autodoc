# 0181 route handler surface audit rule

0181 is a read-only audit before handler execution.

Rules:

- Audit existing route handler surfaces before adding or changing handler code.
- Do not add a new runtime handler in 0181.
- Do not import handler modules for execution.
- Read route handler files as text and AST only.
- Do not call handle_scheduler_route_request.
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
