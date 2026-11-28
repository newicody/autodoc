# 0178 — Context bus scheduler intake reader

## Decision

0178 closes the shortcut left by 0177.

The scheduler intake source is context.bus.jsonl. It reads ContextBusMessage
through runtime.shm_runtime_schema, accepts only topic
github.artifact_dataset.context, and accepts only payload_schema
missipy.github_artifact.dataset_context.v1.

No arbitrary JSON file is a scheduler intake source.

## Why this exists

0176 projects GitHub artifact/server dataset outcomes into existing
event.bus/context.bus facts.

0177 introduced a pure scheduler intake builder, but it could still be driven by
direct JSON input. That is useful for tests, but it is not the operational path.

0178 reconnects the path:

```text
dataset outcome
-> context.bus.jsonl
-> ContextBusMessage.from_mapping(...)
-> scheduler intake candidate
-> SchedulerRouteRequest only with policy_decision_id
```

## Boundary

The reader:

- reads existing `context.bus.jsonl`,
- validates each line through `ContextBusMessage.from_mapping(...)`,
- filters only GitHub artifact dataset context facts,
- builds scheduler intake candidates through the 0177 builder,
- can emit an authorized route request only when `policy_decision_id` is
  explicit.

It does not:

- instantiate EventBus,
- create a parallel bus,
- modify Scheduler.run(),
- call handle_scheduler_route_request,
- bypass Scheduler/policy/zone,
- call GitHub API,
- call network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## Authority

Scheduler/policy/zone remain the authority.
The context bus fact is only an observation source. It is not permission to run.


## Exact rule-test lock phrases — 0178

It reads ContextBusMessage through runtime.shm_runtime_schema.

Additional exact locks:

It accepts only topic github.artifact_dataset.context.

It accepts only payload_schema missipy.github_artifact.dataset_context.v1.
