# 0176 — GitHub artifact dataset bus observation bridge

## Decision

0176 is a bridge to existing event.bus/context.bus messages.

It reuses runtime.shm_runtime_schema EventBusMessage and ContextBusMessage.
It does not create a new bus, does not replace runtime bus schemas, does not
write directly to VisPy, does not modify Scheduler.run(), and does not call
GitHub.

The bridge projects a compact GitHub artifact/server dataset outcome into the
existing SHM runtime observation message types.

```text
dataset outcome -> existing bus facts -> bus_visualization_adapter
```

## Why this exists

0167/0168 prepare GitHub artifact/server dataset synchronization.
0171 locked the existing bus/scheduler boundary.
0172 locked DOT/VisPy as representation.
0174/0175 kept the operational baseline separate from graph heritage.

0176 is the first small operational bridge after that audit chain. It turns the
dataset outcome into existing bus-compatible facts that the rest of the runtime
can already understand.

## Boundary

The bridge:

- imports `EventBusMessage` and `ContextBusMessage` from `runtime.shm_runtime_schema`,
- validates projections through `EventBusMessage.from_mapping()` and
  `ContextBusMessage.from_mapping()`,
- can append to explicit `event.bus.jsonl` and `context.bus.jsonl` files under a
  caller-provided runtime root,
- marks payloads as observation-only,
- marks direct VisPy writes as false,
- marks Scheduler modification as false.

It does not:

- instantiate EventBus,
- subscribe to EventBus,
- create a resident process,
- create a watcher,
- modify Scheduler.run(),
- bypass Scheduler/policy/zone,
- call GitHub API,
- call network,
- execute conversion,
- execute inference,
- write SQL,
- write Qdrant,
- write directly to VisPy.

## GitHub and dataset role

GitHub remains workflow/exchange/validation surface.
The configured server dataset remains a local/server staging and authority
surface for raw/index/history/queue material before later scheduler work.

## Observation role

Bus facts are observation-only. They describe a dataset outcome. They are not a
command path and do not grant scheduling authority.

A future scheduler intake may consume dataset state through an authorized
scheduler path, but that is not implemented here.

## Exact rule-test lock phrases — 0176

It does not write directly to VisPy.

Additional exact locks:

It does not modify Scheduler.run().
