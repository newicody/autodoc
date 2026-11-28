# ControlProxy operational plan — 0107

0107 follows the locked simplification path:

```text
0101 -> 0102 -> 0103 -> 0104 -> 0105 -> 0106 -> 0107
```

## Current decision

The graph structure must reflect the code direction rather than an aspirational
parallel runtime. The ControlProxy route runtime is a subgraph attached to the
micro-kernel path, not an independent architecture.

```text
ROOT_GRAPH: doc/docs/architecture/00_global.dot
root-attached runtime overlay
not an isolated graph
```

## Required reading of the runtime path

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager
RouteRuntimeManager -> ControlFS
RouteRuntimeManager -> mmap/eventfd data plane
RouteRuntimeManager -> generation table / lifecycle / placement
RouteRuntimeManager -> RouteMessageJournal
EventBus = observation only
```

## Boundaries preserved

```text
Dispatcher = EventType -> Handler only
Handler = thin adapter
Specialist branch owns business logic
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution order
ControlProxy does not manage global priorities
Route mmap/eventfd = data plane, not EventBus
```

## Next steps after 0107

0108 should move from graph alignment back to an executable path check. The
recommended next step is a small end-to-end scenario that proves the thin
ControlProxy handler can call RouteRuntimeManager without changing Scheduler,
Dispatcher, PolicyEngine, PriorityQueue or EventBus.

0109 can then identify legacy wrappers that now only delegate to the thin path.

## Prohibited regressions

```text
No ControlProxyBus
No RouteBus
No VisualizationBus
No scheduler-like ControlProxy coordinator
No ControlProxy priority engine
No Dispatcher business logic
No PolicyEngine business logic
No EventBus command path
```
