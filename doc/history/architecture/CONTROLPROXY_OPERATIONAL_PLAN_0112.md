# ControlProxy operational plan — 0112 update

0112 follows the simplification locks:

```text
0101 architecture simplification lock
0102 existing paths audit
0103 RouteRuntimeManager
0104 thin handler to RouteRuntimeManager
0105 priority/admission lock
0106 EventBus/data plane boundary lock
0107 graph root alignment
0108 route-runtime walking skeleton
0109 compatibility wrappers registry
0110 specialist/kernel boundary
0111 explicit /dev/shm runtime root
0112 future NetworkBridge/HardwareBridge boundary declarations
```

## 0112 role

```text
NetworkBridge/HardwareBridge are future adapters behind Handler -> RouteRuntimeManager.
RouteBridgeBoundary records declarations only.
It does not bypass Scheduler, PolicyEngine, PriorityQueue, Dispatcher or Handler.
It does not calculate priority and does not decide policy/zone.
Route mmap/eventfd remains the data plane, not EventBus.
EventBus remains observation only.
```

## Why this is not a new subsystem

0112 intentionally avoids active transport:

```text
No sockets opened
No devices opened
No CLI
No OpenRC service and no resident daemon
No watcher
No active adapter selection
No ControlProxyBus
No RouteBus
No VisualizationBus
stdlib only
```

The bridge boundary is only a stable contract for later phases.  It prevents
future NetworkBridge/HardwareBridge work from being attached directly to
Scheduler, PolicyEngine, PriorityQueue, Dispatcher, EventBus or a specialist.

## Next phase suggestion

0113 should either:

```text
A. add an optional route bridge observation record emitted after a real route event,
   still without active I/O; or
B. start a fake NetworkBridge adapter that consumes an explicit in-memory test
   transport only, if and only if the adapter remains behind Handler -> RouteRuntimeManager.
```

It must not add a daemon, watcher, OpenRC service, socket listener, device opener,
or scheduler-like ControlProxy coordinator.
