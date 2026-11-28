# 0198 controlled dev RouteProxy smoke plan rule

0198 plans the first Bloc B controlled dev execution without executing it.

Rules:

- Read route_pipeline_bloc_a_coherence_record.json from 0197.
- Reuse the existing 0197 Bloc A coherence artifact.
- Reuse tools/run_isolated_route_pipeline_smoke.py.
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
- Do not execute controlled-dev-routeproxy-smoke in 0198.
- Keep execution_allowed_by_0198 false.
- Allow P0199 to unlock controlled dev execution explicitly.
- Require explicit policy_decision_id.
- Require target_runtime_root from Bloc A.
- Require target_isolated_runtime_root from Bloc A.
- Require RouteProxy frame writes to stay inside target_isolated_runtime_root in P0199.
- Require post-execution audit in P0200.
- Require post-audit acceptance in P0200.
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
