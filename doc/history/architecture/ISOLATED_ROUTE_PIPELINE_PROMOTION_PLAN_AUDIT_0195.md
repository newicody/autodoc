# 0195 — Isolated route pipeline promotion plan audit

## Decision

0195 audits the 0194 promotion plan before any controlled dev smoke is executed.

The input is isolated_route_pipeline_promotion_plan.json.
The output is isolated_route_pipeline_promotion_plan_audit.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.
Each bloc or pass must include a systematic phase re-evaluation point so the plan or rules can be adjusted when needed.

It verifies promotion_allowed_by_0194 remains false.
It does not execute the promotion.
It does not call runtime APIs.

## Why this exists

0194 records a promotion intent from the accepted isolated baseline toward
`controlled-dev-routeproxy-smoke`.

Before executing that controlled dev smoke, Bloc A needs a read-only audit that
checks the plan is scoped, coherent, and still non-executing.

This avoids turning a plan into an implicit authorization path.

## Existing-surface reuse decision

0195 does not add a runtime handler, adapter, bus, SQL backend, Qdrant backend,
GitHub client, graph renderer, or inference path.

It reuses the existing artifact created by 0194 and audits it as plain JSON.

## Boundary

0195:

- reads `isolated_route_pipeline_promotion_plan.json`,
- validates `accepted_baseline`,
- validates `controlled-dev-routeproxy-smoke`,
- validates absolute target roots,
- validates `target_isolated_runtime_root` is inside `target_runtime_root`,
- validates required preconditions,
- validates planned steps reuse existing tools,
- validates safety flags,
- writes optional `isolated_route_pipeline_promotion_plan_audit.json`.

0195 does not:

- execute the promotion,
- import runtime handler modules,
- call handle_scheduler_route_command,
- call handle_scheduler_route_request,
- call prepare_route_proxy_runtime,
- call read_route_frame,
- request writer permits,
- call write_route_frame,
- modify Scheduler.run,
- instantiate Scheduler,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy or RouteProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
0195 audits a plan only. It does not approve production route writes.
