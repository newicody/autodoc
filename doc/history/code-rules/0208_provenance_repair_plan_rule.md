# 0208 provenance repair plan rule

0208 plans forward-only provenance repair only.

Rules:

- Read provenance_repair_audit.json from 0207.
- Plan forward-only provenance repair only.
- Select source_baseline_ref candidate.
- Select source_entry_digest candidate.
- Apply doc/code-rules/code_rule.md as the primary rule.
- Keep docs, graph, changelog, manifest, and rule updated with the patch.
- Do not repair source_baseline_ref in 0208.
- Do not repair source_entry_digest in 0208.
- Do not rewrite runtime history in 0208.
- Do not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json.
- Do not write SQL in 0208.
- Do not write Qdrant in 0208.
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
- Do not write ControlProxy or RouteProxy frames.
- Allow P0209 to write provenance_repair_acceptance.json only.
