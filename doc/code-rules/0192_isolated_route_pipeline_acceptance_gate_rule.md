# 0192 isolated route pipeline acceptance gate rule

0192 is the CI-style acceptance gate for the isolated route pipeline baseline.

Rules:

- Read isolated_route_pipeline_artifact_audit.json from 0191.
- Approve only when audit_success is true and issues are empty.
- Approve only when pipeline_success is true.
- Approve only when policy_scoped_queued_count matches downstream counts.
- Approve only when runtime safety flags are false.
- Write only isolated_route_pipeline_acceptance.json as report output.
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
