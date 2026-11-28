# 0199 controlled dev RouteProxy smoke execution rule

0199 executes controlled dev RouteProxy smoke by reusing the existing pipeline tool.

Rules:

- Read controlled_dev_routeproxy_smoke_plan.json from 0198.
- Reuse the existing 0198 plan artifact.
- Reuse tools/run_isolated_route_pipeline_smoke.py.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Allow controlled-dev-routeproxy-smoke execution in 0199.
- Require explicit policy_decision_id.
- Require target_runtime_root from the plan.
- Require target_isolated_runtime_root from the plan.
- Write RouteProxy frames only under target_isolated_runtime_root.
- Keep scheduler.route_requests.jsonl append-only.
- Use policy-scoped queue for the policy_decision_id.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Do not approve production route writes.
- Do not write ControlProxy frames.
- Do not modify Scheduler.run.
- Do not call GitHub API.
- Do not use network.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
- Require P0200 post-execution audit.
- Require P0200 post-audit acceptance.
