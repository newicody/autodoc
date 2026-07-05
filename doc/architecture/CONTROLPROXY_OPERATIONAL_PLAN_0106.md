# ControlProxy operational plan — 0106

0106 follows the simplification lock from 0101, the existing-paths audit from
0102, the `RouteRuntimeManager` introduction from 0103, the thin handler path
from 0104, and the priority/admission lock from 0105.

## Decision

The project now treats route mmap/eventfd as a data plane and keeps EventBus as
the single kernel observation path.

```text
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
RouteMessageJournal = drained route message journal, not EventBus
Visualization adapter = existing EventBus/context reader, not bus owner
```

## No second bus

The following names and concepts are intentionally rejected:

```text
No ControlProxyBus
No RouteBus
No VisualizationBus
No bus created by ControlProxy
No bus created by RouteRuntimeManager
No bus owned by visualization adapters
No mmap/eventfd command bus
```

## Current live path

```text
Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> RouteRuntimeManager
-> ControlFS + mmap/eventfd data plane
```

The EventBus observes; it does not command.

## Next patch

0107 should update the architecture graph set, not runtime code. It must make
`doc/docs/architecture/00_global.dot` and the runtime overlay consistent with
this vocabulary:

```text
command path: Scheduler -> Dispatcher -> Handler
runtime data plane: RouteRuntimeManager -> mmap/eventfd
observation path: EventBus readers
context path: ContextGate / GlobalContextSnapshot
projection/search path: Qdrant only as projection
```
