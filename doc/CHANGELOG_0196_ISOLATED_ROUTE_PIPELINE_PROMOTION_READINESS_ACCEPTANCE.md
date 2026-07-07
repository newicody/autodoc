# Changelog — 0196 Isolated route pipeline promotion readiness acceptance

## Added

- Acceptance gate for `isolated_route_pipeline_promotion_plan_audit.json`.
- `isolated_route_pipeline_promotion_readiness_acceptance.json` report.
- `controlled_dev_smoke_ready` readiness signal.
- `execution_allowed_by_0196=false` safety lock.
- `phase_re_evaluation_required_before_execution=true` lock for P0197.
- Documentation, graph, changelog, manifest, and code-rule entry for the patch.

## Not changed

- No controlled dev smoke execution.
- No runtime handler import.
- No runtime handler call.
- No new adapter, bus, SQL backend, Qdrant backend, GitHub client, graph
  renderer, or inference path.
- No Scheduler.run modification.
- No production route write.
