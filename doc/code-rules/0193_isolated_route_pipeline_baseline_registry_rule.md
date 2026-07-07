# 0193 isolated route pipeline baseline registry rule

0193 registers accepted isolated route pipeline baselines.

Rules:

- Read isolated_route_pipeline_acceptance.json from 0192.
- Register only when acceptance_approved is true.
- Register only accepted_baseline isolated-route-pipeline-write-read-v1.
- Write only isolated_route_pipeline_baseline_registry.jsonl.
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
