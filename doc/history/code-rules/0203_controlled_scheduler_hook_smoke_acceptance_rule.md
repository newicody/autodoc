# 0203 controlled Scheduler hook smoke acceptance rule

0203 executes a controlled Scheduler hook smoke only.

Rules:

- Read scheduler_hook_dry_run_plan.json from 0202.
- Reuse the existing 0202 plan artifact.
- Reuse tools/run_isolated_route_pipeline_smoke.py.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Allow controlled Scheduler hook smoke execution in 0203.
- Require explicit policy_decision_id.
- Require context.bus.jsonl.
- Require RouteProxy writes to stay inside target_isolated_runtime_root.
- Require ControlProxy frames false.
- Require Scheduler modified false.
- Require network used false.
- Do not execute Scheduler.run in 0203.
- Do not modify Scheduler.run in 0203.
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
- Do not approve production route writes.
- Do not write ControlProxy frames.
- Do not call GitHub API.
- Do not use network.
- Do not write SQL.
- Do not write Qdrant.
- Do not write directly to VisPy.
- Open Bloc D only after acceptance.
