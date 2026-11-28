# 0199 — Controlled dev RouteProxy smoke execution

## Decision

0199 executes the controlled dev RouteProxy smoke by reusing the existing pipeline tool.

The input is controlled_dev_routeproxy_smoke_plan.json.
The output is controlled_dev_routeproxy_smoke_execution.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

P0199 explicitly unlocks execution.
The execution surface reused is tools/run_isolated_route_pipeline_smoke.py.
P0200 must perform post-execution audit and acceptance.

## Why this exists

Bloc B is the first execution-oriented bloc.

0198 proved that the controlled dev execution can be unlocked. 0199 performs
that execution without adding a new handler, adapter, bus, SQL backend, Qdrant
backend, GitHub client, graph renderer, or inference path.

## Existing-surface reuse decision

0199 reuses:

- `controlled_dev_routeproxy_smoke_plan.json` from 0198,
- `tools/run_isolated_route_pipeline_smoke.py` as the execution surface,
- `target_runtime_root` and `target_isolated_runtime_root` from the plan,
- the explicit `policy_decision_id` from the plan.

## Boundary

0199:

- reads `controlled_dev_routeproxy_smoke_plan.json`,
- validates `plan_ready`,
- validates `execution_can_be_unlocked_by_p0199`,
- validates explicit `policy_decision_id`,
- validates target roots,
- executes `tools/run_isolated_route_pipeline_smoke.py`,
- writes `isolated_route_pipeline_smoke.json` under `target_runtime_root`,
- writes optional `controlled_dev_routeproxy_smoke_execution.json`.

0199 does not:

- add a new runtime handler,
- add a new adapter,
- add a new bus,
- modify Scheduler.run,
- write ControlProxy frames,
- call GitHub API,
- use network,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Execution unlock policy

Execution locks are phase gates, not permanent prohibitions.

0199 unlocks only the controlled dev RouteProxy smoke scope. It does not unlock
production route roots or Scheduler integration.

The RouteProxy frame writes must stay inside `target_isolated_runtime_root`.

## Required follow-up

P0200 must perform:

- post-execution artifact audit,
- post-audit acceptance,
- controlled dev registry or Bloc B coherence decision.

## Authority

Scheduler/policy/zone remain the authority.
0199 executes a controlled dev smoke only. It does not approve production route writes.
