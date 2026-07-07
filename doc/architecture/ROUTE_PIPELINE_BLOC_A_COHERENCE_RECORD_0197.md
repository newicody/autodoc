# 0197 — Route pipeline Bloc A coherence record

## Decision

0197 closes Bloc A with a coherence record and phase re-evaluation.

The input is isolated_route_pipeline_promotion_readiness_acceptance.json.
The output is route_pipeline_bloc_a_coherence_record.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

Execution locks are phase gates, not permanent prohibitions.
Bloc B may unlock controlled dev execution explicitly when required.
The next recommended patch is P0198 controlled dev smoke plan.

## Why this exists

Bloc A stabilized the accepted isolated prototype and prepared a controlled dev
promotion without executing it.

0197 records that Bloc A is coherent, complete, and ready to hand off to Bloc B.

It also records the important policy clarification: the final prototype is an
execution. Therefore safety locks must be released when a later execution phase
explicitly requires it and passes the proper gates.

## Existing-surface reuse decision

0197 does not add a runtime handler, adapter, bus, SQL backend, Qdrant backend,
GitHub client, graph renderer, or inference path.

It reuses the existing artifact created by 0196 and records coherence as plain
JSON.

## Boundary

0197:

- reads `isolated_route_pipeline_promotion_readiness_acceptance.json`,
- validates Bloc A readiness,
- validates future controlled dev target,
- validates existing-surface reuse,
- validates safety flags,
- records phase re-evaluation,
- records that Bloc B may explicitly unlock controlled dev execution,
- writes optional `route_pipeline_bloc_a_coherence_record.json`.

0197 does not:

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

Bloc A is accepted when:

- P0195 promotion plan audit is clean,
- P0196 readiness acceptance is clean,
- P0197 coherence record is clean,
- no new runtime surface was introduced,
- docs, graph, changelog, manifest, and rules are updated.

If any of those fail, Bloc A remains open and the plan must be adjusted before
Bloc B starts.

## Execution unlock policy

`execution_allowed_by_0197` remains false because P0197 is not the execution
patch.

`future_execution_can_be_unlocked` is true because the final prototype is an
execution. A later execution patch may unlock execution only with:

- explicit execution scope,
- explicit `policy_decision_id`,
- reuse/adaptation of existing tools first,
- updated docs/graph/changelog/manifest/rules,
- post-execution audit,
- post-audit acceptance.

## Authority

Scheduler/policy/zone remain the authority.
0197 closes preparation only. It does not approve production route writes.
