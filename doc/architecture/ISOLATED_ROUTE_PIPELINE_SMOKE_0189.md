# 0189 — Isolated route pipeline smoke

## Decision

0189 runs the isolated route pipeline end to end.

It reuses 0179, 0184, 0185, 0186, 0187, and 0188.

It writes RouteProxy frames only inside isolated_runtime_root.
It must not modify Scheduler.run.
It must not instantiate EventBus.
It must not write ControlProxy frames.

This is the first isolated write/read pipeline prototype.

## Why this exists

0188 proved that an isolated RouteProxy frame can be written and read back.

0189 consolidates the staged smoke chain into one reviewable command. It does
not add a new runtime handler and does not create a new authority path. It only
orchestrates already validated local stages with an explicit isolated runtime
root.

## 0190 policy-scoped queue lock

0190 keeps 0189 as the isolated pipeline smoke, but fixes accumulation across
multiple runs. `scheduler.route_requests.jsonl` remains append-only. Before
0184 is called, 0189 writes a fresh
`scheduler.route_requests.policy_scoped.jsonl` containing only route requests
with the current `policy_decision_id`.

Downstream stages must read the policy-scoped queue, not the append-only queue.

## Pipeline

```text
context.bus.jsonl
-> 0179 scheduler.route_requests.jsonl
-> 0190 scheduler.route_requests.policy_scoped.jsonl
-> 0184 route_request_to_command_dry_run_plan.jsonl
-> 0185 scheduler_route_handler_command_smoke.jsonl
-> 0186 isolated_handler_execution_plan.jsonl
-> 0187 isolated_scheduler_route_handler_smoke.jsonl
-> 0188 isolated_scheduler_route_handler_readback_smoke.jsonl
-> isolated_route_pipeline_smoke.json
```

## Boundary

0189:

- reads `context.bus.jsonl`,
- requires explicit `policy_decision_id`,
- requires explicit `isolated_runtime_root`,
- reuses existing 0179 and 0184 through 0188 stages,
- writes a consolidated `isolated_route_pipeline_smoke.json` report.

0189 does not:

- add a new runtime handler,
- modify Scheduler.run,
- instantiate Scheduler,
- instantiate EventBus,
- create a parallel bus,
- write ControlProxy frames,
- call GitHub API,
- use network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
0189 is an isolated prototype smoke, not permission to write production route
frames.
