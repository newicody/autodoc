# 0196 isolated route pipeline promotion readiness acceptance rule

0196 accepts readiness after a clean 0195 audit without executing promotion.

Rules:

- Read isolated_route_pipeline_promotion_plan_audit.json from 0195.
- Reuse the existing 0195 promotion plan audit artifact.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Require audit_success true.
- Require promotion_ready true.
- Require promotion_allowed_by_0194 false.
- Keep execution_allowed_by_0196 false.
- Require phase re-evaluation before execution.
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
