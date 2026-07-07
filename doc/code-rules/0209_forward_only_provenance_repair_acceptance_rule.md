# 0209 forward-only provenance repair acceptance rule

0209 writes forward-only provenance repair acceptance only.

Rules:

- Read provenance_repair_plan.json from 0208.
- Write provenance_repair_acceptance.json only.
- Repair source_baseline_ref by forward-only artifact.
- Repair source_entry_digest by forward-only artifact.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not rewrite runtime history in 0209.
- Do not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
- Do not write SQL in 0209.
- Do not write Qdrant in 0209.
- Do not add a new SQL backend.
- Do not add a new Qdrant backend.
- Do not add a new runtime handler.
- Do not add a new adapter.
- Do not add a new bus.
- Do not add a new Scheduler.
- Do not add a new ControlProxy runtime.
- Do not add a new RouteProxy runtime.
- Do not call GitHub API.
- Do not use network.
- Do not execute Scheduler.run.
- Do not modify Scheduler.run.
- Do not import runtime handler modules.
- Do not call mark_route_frame_stale.
- Do not write ControlProxy or RouteProxy frames in 0209.
- Open Bloc F only after acceptance.
