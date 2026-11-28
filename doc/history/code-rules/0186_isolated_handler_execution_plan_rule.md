# 0186 isolated handler execution plan rule

0186 plans a future isolated handler execution without running RouteProxyRuntime.

Rules:

- Read scheduler_route_handler_command_smoke.jsonl from 0185.
- Build only isolated_handler_execution_plan.jsonl.
- Resolve RouteProxyRuntimePolicy by text/AST only.
- Do not import route_proxy_runtime_minimal.
- Do not import runtime handler modules.
- Do not call prepare_route_proxy_runtime.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
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
