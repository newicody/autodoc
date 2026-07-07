# 0203 — Controlled Scheduler hook smoke acceptance

## Decision

0203 closes Bloc C with a controlled Scheduler hook smoke and acceptance.

The input is scheduler_hook_dry_run_plan.json.
The output is controlled_scheduler_hook_smoke_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
docs, graph, changelog, manifest, and rule are updated with the patch.

0203 unlocks controlled Scheduler hook smoke execution.
0203 still does not execute Scheduler.run.
The execution surface reused is tools/run_isolated_route_pipeline_smoke.py.
The next recommended patch is P0204 ControlProxy contract audit.

## Why this exists

0202 proved that a controlled Scheduler hook smoke can be planned from existing
surfaces. 0203 executes that smoke without adding a new Scheduler hook
implementation and without modifying Scheduler.run.

This closes Bloc C and proves that the Scheduler-oriented path can reuse the
existing route pipeline execution surface.

## Boundary

0203:

- reads `scheduler_hook_dry_run_plan.json`,
- requires explicit `policy_decision_id`,
- requires `context.bus.jsonl`,
- reuses `tools/run_isolated_route_pipeline_smoke.py`,
- writes `controlled_scheduler_hook_smoke_pipeline.json`,
- writes optional `controlled_scheduler_hook_smoke_acceptance.json`,
- accepts Bloc C when the controlled smoke succeeds.

0203 does not:

- execute Scheduler.run,
- modify Scheduler.run,
- add a new Scheduler hook implementation,
- add a new runtime handler,
- add a new adapter,
- add a new bus,
- write ControlProxy frames,
- call GitHub API,
- use network,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Acceptance

Bloc C is accepted as `controlled-scheduler-hook-routeproxy-write-read-v1` when:

- P0202 plan is clean,
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

Bloc D starts with P0204 ControlProxy contract audit.
