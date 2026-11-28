# 0198 — Controlled dev RouteProxy smoke plan

## Decision

0198 opens Bloc B with a controlled dev RouteProxy smoke plan.

The input is route_pipeline_bloc_a_coherence_record.json.
The output is controlled_dev_routeproxy_smoke_plan.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

P0198 plans execution but keeps execution_allowed_by_0198 false.
P0199 may explicitly unlock controlled-dev-routeproxy-smoke.
The execution surface to reuse is tools/run_isolated_route_pipeline_smoke.py.

## Why this exists

Bloc A proved that the isolated route pipeline is accepted and coherent.

Bloc B is the first execution-oriented bloc. It must not invent a new execution
surface if the existing isolated route pipeline smoke tool can be reused.

0198 turns the Bloc A coherence record into a controlled dev execution plan for
P0199.

## Existing-surface reuse decision

0198 does not add a runtime handler, adapter, bus, SQL backend, Qdrant backend,
GitHub client, graph renderer, or inference path.

It reuses:

- `route_pipeline_bloc_a_coherence_record.json` from 0197,
- `tools/run_isolated_route_pipeline_smoke.py` as the execution surface planned
  for P0199,
- the target roots already carried by Bloc A.

## Boundary

0198:

- reads `route_pipeline_bloc_a_coherence_record.json`,
- validates Bloc A is complete,
- validates future execution may be unlocked,
- validates target roots,
- requires explicit `policy_decision_id`,
- writes optional `controlled_dev_routeproxy_smoke_plan.json`.

0198 does not:

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

## Execution unlock policy

Execution locks are phase gates, not permanent prohibitions.

P0198 remains a plan. P0199 may unlock controlled dev execution explicitly if it:

- reuses `tools/run_isolated_route_pipeline_smoke.py`,
- uses an explicit `policy_decision_id`,
- writes RouteProxy frames only under `target_isolated_runtime_root`,
- keeps `scheduler.route_requests.jsonl` append-only,
- uses a fresh policy-scoped queue,
- avoids ControlProxy frames,
- avoids Scheduler.run modification,
- avoids GitHub API/network,
- updates docs, graph, changelog, manifest, and rules.

## Authority

Scheduler/policy/zone remain the authority.
0198 plans a controlled dev smoke only. It does not approve production route writes.
