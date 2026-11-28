# 0190 — Isolated route pipeline policy-scoped queue

## Decision

0190 fixes pipeline replay caused by the append-only route request queue.

`scheduler.route_requests.jsonl` remains append-only.
`scheduler.route_requests.policy_scoped.jsonl` is rebuilt for the current
`policy_decision_id` before downstream pipeline stages run.

Downstream 0184 through 0188 stages read only the policy-scoped queue.

## Why this exists

0189 successfully proved the isolated write/read pipeline, but a manual run
showed:

```text
queued_count: 1
command_built_count: 2
handler_executed_count: 2
readback_count: 2
```

That means an old queue entry was replayed because
`scheduler.route_requests.jsonl` is append-only.

0190 preserves the append-only audit trail while making the pipeline run
deterministic and scoped to the current policy decision.

## Boundary

0190:

- reads the append-only `scheduler.route_requests.jsonl`,
- filters by exact `policy_decision_id`,
- writes fresh `scheduler.route_requests.policy_scoped.jsonl`,
- passes the scoped queue to 0184,
- reports `policy_scoped_queued_count`.

0190 does not:

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
