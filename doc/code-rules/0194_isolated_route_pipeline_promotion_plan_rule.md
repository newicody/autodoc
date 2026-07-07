# 0194 isolated route pipeline promotion plan rule

0194 plans a controlled dev promotion from the accepted isolated baseline.

Rules:

- Read isolated_route_pipeline_baseline_registry.jsonl from 0193.
- Plan only controlled-dev-routeproxy-smoke.
- Require explicit target_runtime_root.
- Require explicit target_isolated_runtime_root.
- Do not execute the promotion.
- Do not approve production route writes.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
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
