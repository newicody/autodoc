# 0103 — RouteRuntimeManager

0103 introduces `RouteRuntimeManager` as the single importable runtime facade for the ControlProxy / ControlFS route primitives.

It is deliberately not a new coordinator for Scheduler work.

```text
RouteRuntimeManager is not a scheduler-like coordinator.
```

## Locked responsibilities

```text
Scheduler = loop + time + queue + priority
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic ordering
Dispatcher = EventType -> Handler only
Handler = thin adapter
Specialist branch owns business logic
ControlProxy / RouteRuntimeManager = route/mmap/controlfs runtime transport
EventBus = observation only
Route mmap/eventfd is a data plane, not EventBus
```

## What the manager does

`RouteRuntimeManager` receives explicit roots:

```text
controlfs_root
runtime_root
```

It then composes existing route runtime primitives:

```text
materialize_generation()
activate_generation()
mark_draining()
mark_closed()
cleanup_closed()
load_table()
```

The manager wraps:

```text
0091-r2 generation table
0092 generation lifecycle
0094 route generation lock
0095 locked materializer
```

The manager receives an already-decided `RoutePrepareDecision`. It does not authorize work and does not calculate priority.

## Guardrails

```text
No CLI
No OpenRC service and no resident daemon
No watcher
No Scheduler.run() modification
No PriorityQueue, Dispatcher or Component tick contract modification
No global priority management
No policy decision and no zone authority in ControlProxy
No EventBus creation and no bus duplication
Route mmap/eventfd is a data plane, not EventBus
EventBus remains observation only
Dispatcher remains EventType -> Handler only
PolicyEngine remains minimal admission before queue
Specialist branch owns business logic
```

## Why this is not the rejected 0101 coordinator

The rejected direction was a `ControlProxyRouteCoordinator` that could become a second Scheduler.

0103 avoids that by making the new object a runtime manager only:

```text
Scheduler.run()
-> Dispatcher
-> thin ControlProxy handler
-> RouteRuntimeManager
-> ControlFS + route data plane
```

It has no EventBus ownership, no priority ownership, no admission authority and no specialist logic.
