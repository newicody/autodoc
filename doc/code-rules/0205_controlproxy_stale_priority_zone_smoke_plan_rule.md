# 0205 ControlProxy stale priority zone smoke plan rule

0205 plans stale priority zone behavior only.

Rules:

- Read controlproxy_contract_audit.json from 0204.
- Plan stale priority zone behavior only.
- Reuse existing ControlProxy and RouteProxy contract surfaces.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not write ControlProxy frames in 0205.
- Do not write RouteProxy frames in 0205.
- Do not call mark_route_frame_stale in 0205.
- Do not call prepare_route_proxy_runtime in 0205.
- Do not call read_route_frame in 0205.
- Do not request writer permits in 0205.
- Do not call write_route_frame in 0205.
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
- ControlProxy remains coordination, not business authority.
- Scheduler/policy/zone remain authority.
- RouteProxy remains the fast data-plane frame surface.
- Do not execute Scheduler.run in 0205.
- Do not modify Scheduler.run in 0205.
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
- Allow P0206 to unlock controlled stale priority zone smoke explicitly.
