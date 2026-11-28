# 0204 ControlProxy contract audit rule

0204 audits existing ControlProxy and RouteProxy contract surfaces only.

Rules:

- Read controlled_scheduler_hook_smoke_acceptance.json from 0203.
- Audit existing ControlProxy and RouteProxy contract surfaces before planning stale priority zone behavior.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Reuse controlproxy_scheduler_handler.py.
- Reuse route_proxy_runtime_minimal.py.
- Reuse scheduler_route_adapter.py.
- Reuse scheduler_route_handler_minimal.py.
- Reuse shm_runtime_schema.py for observation schema only.
- ControlProxy is a coordination surface, not business authority.
- Scheduler/policy/zone remain authority.
- RouteProxy remains the fast data-plane frame surface.
- Do not add a new ControlProxy runtime.
- Do not add a new RouteProxy runtime.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new Scheduler.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Do not execute Scheduler.run in 0204.
- Do not modify Scheduler.run in 0204.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
- Do not write ControlProxy frames in 0204.
- Do not write RouteProxy frames in 0204.
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
- Allow P0205 to plan stale priority zone behavior only after audit.
