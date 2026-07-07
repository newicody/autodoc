# 0201 Scheduler integration surface audit rule

0201 audits existing Scheduler integration surfaces before any hook plan.

Rules:

- Read controlled_dev_routeproxy_smoke_post_execution_acceptance.json from 0200.
- Audit existing Scheduler integration surfaces before planning a hook.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Reuse scheduler_route_adapter.py.
- Reuse scheduler_route_handler_minimal.py.
- Reuse scheduler_route_handshake.py.
- Reuse controlproxy_scheduler_handler.py only as an existing surface candidate.
- Reuse route_proxy_runtime_minimal.py only as an existing surface candidate.
- Reuse shm_runtime_schema.py for bus schema observation only.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new Scheduler.
- Do not add a new RouteProxy runtime.
- Do not add a new ControlProxy runtime.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Do not execute Scheduler.run in 0201.
- Do not approve Scheduler integration yet.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
- Do not write ControlProxy or RouteProxy frames.
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
- Preserve missing source_baseline_ref or source_entry_digest as a provenance repair item.
