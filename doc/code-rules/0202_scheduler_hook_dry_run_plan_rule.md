# 0202 Scheduler hook dry-run plan rule

0202 creates a dry-run plan only.

Rules:

- Read scheduler_integration_surface_audit.json from 0201.
- Reuse the existing audited surfaces before adding new code.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not add a new Scheduler hook implementation.
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
- Do not execute Scheduler.run in 0202.
- Do not write RouteProxy frames in 0202.
- Do not write ControlProxy frames in 0202.
- Do not instantiate Scheduler.
- Do not instantiate EventBus.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
- Do not call GitHub API.
- Do not use network.
- Do not execute conversion.
- Do not execute inference.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
- Allow P0203 to unlock a controlled Scheduler hook smoke explicitly.
- Require adapter -> command builder -> minimal handler -> readback.
- Carry provenance repair items forward.
