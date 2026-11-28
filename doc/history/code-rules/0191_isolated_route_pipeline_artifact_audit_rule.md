# 0191 isolated route pipeline artifact audit rule

0191 validates saved isolated pipeline artifacts without runtime execution.

Rules:

- Read isolated_route_pipeline_smoke.json from 0190.
- Validate artifact files and counters only.
- Verify 0184 consumed scheduler.route_requests.policy_scoped.jsonl.
- Verify policy_scoped_queued_count matches downstream item counts.
- Verify handler smoke frame paths stay under isolated_runtime_root.
- Verify readback reports did not call the handler or write frames.
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
