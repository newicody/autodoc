# 0206 ControlProxy RouteProxy coherence acceptance rule

0206 executes controlled coherence acceptance only.

Rules:

- Read controlproxy_stale_priority_zone_smoke_plan.json from 0205.
- Reuse the existing 0205 plan artifact.
- Reuse tools/run_isolated_route_pipeline_smoke.py.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Allow controlled stale priority zone coherence smoke execution in 0206.
- Require explicit policy_decision_id.
- Require context.bus.jsonl.
- Require RouteProxy writes to stay inside target_isolated_runtime_root.
- Require ControlProxy frames false.
- Require Scheduler modified false.
- Require network used false.
- Do not execute Scheduler.run in 0206.
- Do not modify Scheduler.run in 0206.
- Do not add a new ControlProxy runtime.
- Do not add a new RouteProxy runtime.
- Do not add a new Scheduler hook implementation.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new Scheduler.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new GitHub client.
- Do not add a new graph renderer.
- Do not add a new inference path.
- Do not call mark_route_frame_stale directly in 0206.
- Do not approve production route writes.
- Do not write ControlProxy frames in 0206.
- Do not call GitHub API.
- Do not use network.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
- Open Bloc E only after acceptance.
