# ControlProxy operational plan — 0109

0109 compatibility wrapper cleanup is the bridge between the 0108 walking skeleton and the next runtime cleanup phases.

## Decision

```text
prepare_route_for_scheduler and handle_scheduler_route_request remain compatibility wrappers.
do not extend legacy wrappers.
New runtime effects go through Handler -> RouteRuntimeManager.
```

## Current path

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

## Boundaries kept

```text
No Scheduler.run() modification
Dispatcher = EventType -> Handler only
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution order
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
No ControlProxyBus
No RouteBus
No VisualizationBus
Specialist branch owns business logic
No scheduler-like ControlProxy coordinator
```

## Next phases

```text
0110: route legacy wrappers through RouteRuntimeManager when the payload shape is compatible.
0111: full Scheduler.run() integration test only if handler registration is stable.
0112: remove or deprecate legacy wrappers after callers converge.
```
