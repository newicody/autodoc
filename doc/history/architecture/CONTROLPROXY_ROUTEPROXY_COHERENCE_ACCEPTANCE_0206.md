# 0206 — ControlProxy / RouteProxy coherence acceptance

## Decision

0206 closes Bloc D with ControlProxy/RouteProxy coherence acceptance.

The input is controlproxy_stale_priority_zone_smoke_plan.json.
The output is controlproxy_routeproxy_coherence_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0206 unlocks controlled stale priority zone coherence smoke execution.
0206 still does not execute Scheduler.run.
0206 still does not write ControlProxy frames.
The execution surface reused is tools/run_isolated_route_pipeline_smoke.py.
The next recommended patch is P0207 provenance repair audit.

## Why this exists

0205 planned stale, priority, and zone coherence from existing contract surfaces.
0206 executes a bounded RouteProxy write/readback smoke through the existing
pipeline and accepts the ControlProxy/RouteProxy contract without adding a new
ControlProxy runtime.

## Boundary

0206:

- reads `controlproxy_stale_priority_zone_smoke_plan.json`,
- requires explicit `policy_decision_id`,
- requires `context.bus.jsonl`,
- reuses `tools/run_isolated_route_pipeline_smoke.py`,
- writes `isolated_route_pipeline_smoke.json`,
- writes optional `controlproxy_routeproxy_coherence_acceptance.json`,
- closes Bloc D when coherence is accepted.

0206 does not:

- execute Scheduler.run,
- modify Scheduler.run,
- add a new ControlProxy runtime,
- add a new RouteProxy runtime,
- add a new Scheduler hook implementation,
- add a new runtime handler,
- add a new adapter,
- add a new bus,
- call mark_route_frame_stale directly,
- write ControlProxy frames,
- call GitHub API,
- use network,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Acceptance

Bloc D is accepted as `controlproxy-routeproxy-stale-priority-zone-coherence-v1` when:

- P0205 plan is clean,
- explicit policy decision is present,
- existing execution surface is reused,
- pipeline success is true,
- one policy-scoped request is executed,
- one RouteProxy frame is written,
- one RouteProxy frame is read back,
- ControlProxy frames remain false,
- Scheduler modified remains false,
- Scheduler.run remains unexecuted,
- network remains unused.

## Next

Bloc E starts with P0207 provenance repair audit.
