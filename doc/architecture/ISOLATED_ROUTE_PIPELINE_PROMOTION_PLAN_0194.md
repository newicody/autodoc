# 0194 — Isolated route pipeline promotion plan

## Decision

0194 plans the next promotion step from the accepted isolated baseline.

The input is isolated_route_pipeline_baseline_registry.jsonl.
The output is isolated_route_pipeline_promotion_plan.json.

It plans controlled-dev-routeproxy-smoke.
It does not execute the promotion.
It does not call runtime APIs.

0194 is not a production promotion.

## Why this exists

0193 registered the accepted isolated baseline. The next safe step is not to jump
to production, but to plan a controlled dev smoke rooted in explicit target
directories.

0194 creates that plan and records the preconditions before any future patch is
allowed to execute a dev smoke.

## Boundary

0194:

- reads `isolated_route_pipeline_baseline_registry.jsonl`,
- selects the latest or requested `baseline_ref`,
- verifies the accepted baseline and counts,
- verifies safety flags,
- records `target_runtime_root`,
- records `target_isolated_runtime_root`,
- writes `isolated_route_pipeline_promotion_plan.json`.

0194 does not:

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

## Promotion target

The only target planned by 0194 is:

```text
controlled-dev-routeproxy-smoke
```

A future patch may execute that target only if it uses:

- a new explicit `policy_decision_id`,
- a fresh policy-scoped queue,
- an explicit `target_runtime_root`,
- an explicit `target_isolated_runtime_root`,
- post-run 0191 audit,
- post-audit 0192 acceptance gate.

## Authority

Scheduler/policy/zone remain the authority.
0194 records promotion intent only. It does not approve production route writes.
