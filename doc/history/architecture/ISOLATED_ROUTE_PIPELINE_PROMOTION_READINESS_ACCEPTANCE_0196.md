# 0196 — Isolated route pipeline promotion readiness acceptance

## Decision

0196 accepts the clean 0195 promotion plan audit as ready for a later controlled dev smoke.

The input is isolated_route_pipeline_promotion_plan_audit.json.
The output is isolated_route_pipeline_promotion_readiness_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

It accepts readiness but keeps execution_allowed_by_0196 false.
It does not execute controlled-dev-routeproxy-smoke.
It does not call runtime APIs.

The next required patch is P0197 Bloc A coherence record.

## Why this exists

Bloc A must end with controlled discipline: plan, audit, readiness acceptance,
then a final bloc coherence record.

0196 proves that the P0194 plan and P0195 audit are clean enough for the next
bloc decision, while still refusing to execute the dev smoke directly.

## Existing-surface reuse decision

0196 does not add a runtime handler, adapter, bus, SQL backend, Qdrant backend,
GitHub client, graph renderer, or inference path.

It reuses the existing artifact created by 0195 and accepts it as plain JSON.

## Boundary

0196:

- reads `isolated_route_pipeline_promotion_plan_audit.json`,
- validates `audit_success`,
- validates `controlled-dev-routeproxy-smoke`,
- validates `promotion_ready`,
- validates `promotion_allowed_by_0194` remains false,
- validates new-surface flags remain false,
- validates runtime safety flags remain false,
- writes optional `isolated_route_pipeline_promotion_readiness_acceptance.json`.

0196 does not:

- execute controlled-dev-routeproxy-smoke,
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

## Phase re-evaluation

0196 records `phase_re_evaluation_required_before_execution=true`.

That forces P0197 to re-evaluate Bloc A before Bloc B is opened. The plan or
rules may be adjusted at that point if needed.

## Authority

Scheduler/policy/zone remain the authority.
0196 accepts readiness only. It does not approve production route writes.
