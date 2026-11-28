# Scheduler/EventBus bootstrap readiness - 0243

## Intent

This patch checks Scheduler/EventBus bootstrap readiness from the validated
production server INI and the 0242 component registry.

It confirms that:

```text
Scheduler exists and is enabled
EventBus exists and is enabled
Scheduler is command path
EventBus is observation path
both are present in dependency order
```

No factory is imported or called in this phase.

## Boundary

0243 is readiness-only. It does not start OpenRC, create Scheduler/EventBus,
start threads, publish EventBus events, call GitHub, write PostgreSQL, or write
Qdrant.

## Next step

0244 can use this readiness result to define the OpenRC launcher
`configtest/start/stop/status` surface. Runtime instantiation remains separate
and must continue to respect the rule that components do not start threads in
`__init__`.
