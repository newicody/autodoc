# Changelog — 0198 Controlled dev RouteProxy smoke plan

## Added

- Bloc B controlled dev RouteProxy smoke plan.
- Reuse lock for `tools/run_isolated_route_pipeline_smoke.py`.
- Explicit P0199 execution unlock plan.
- Explicit `policy_decision_id` requirement.
- `execution_allowed_by_0198=false`.
- `execution_can_be_unlocked_by_p0199=true` when the plan is clean.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No controlled dev smoke execution in 0198.
- No runtime handler import.
- No runtime handler call.
- No new adapter, bus, SQL backend, Qdrant backend, GitHub client, graph
  renderer, or inference path.
- No Scheduler.run modification.
- No production route write.
