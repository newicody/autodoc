# 0195 isolated route pipeline promotion plan audit rule

0195 audits the 0194 promotion plan without executing it.

Rules:

- Read isolated_route_pipeline_promotion_plan.json from 0194.
- Reuse the existing 0194 promotion plan artifact.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Re-evaluate the active phase before moving forward and update the plan or rules when needed.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Verify promotion_allowed_by_0194 remains false.
- Verify promotion_ready is true.
- Verify target_runtime_root is absolute.
- Verify target_isolated_runtime_root is absolute and inside target_runtime_root.
- Verify planned dev-smoke-run reuses tools/run_isolated_route_pipeline_smoke.py.
- Do not execute controlled-dev-routeproxy-smoke.
- Do not approve production route writes.
- Do not import runtime handler modules.
- Do not call handle_scheduler_route_command.
- Do not call handle_scheduler_route_request.
- Do not call prepare_route_proxy_runtime.
- Do not call read_route_frame.
- Do not request writer permits.
- Do not call write_route_frame.
- Do not write ControlProxy or RouteProxy frames.
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
