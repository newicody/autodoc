# Route bridge boundary — 0112

0112 prepares the future NetworkBridge/HardwareBridge boundary without
implementing active I/O.

## Locked decision

```text
NetworkBridge/HardwareBridge are future adapters behind Handler -> RouteRuntimeManager.
RouteBridgeBoundary is a declaration layer only.
It does not bypass Scheduler, PolicyEngine, PriorityQueue, Dispatcher or Handler.
It does not calculate priority and does not decide policy/zone.
Route mmap/eventfd remains the data plane, not EventBus.
EventBus remains observation only.
```

## What 0112 adds

```text
RouteBridgeBoundarySpec
RouteBridgePlan
build_route_bridge_plan()
route_bridge_spec_from_mapping()
```

The plan has `effect="none"` in this phase.  Even an enabled declaration does
not open a socket, open a device, subscribe to EventBus, create a bus, launch a
watcher, start a daemon, or select a real adapter.

## Guardrails

```text
No sockets opened
No devices opened
No CLI
No OpenRC service and no resident daemon
No watcher
No Scheduler.run() modification
No Dispatcher expansion
No PriorityQueue change
No PolicyEngine expansion
No EventBus creation
No ControlProxyBus
No RouteBus
No VisualizationBus
stdlib only
```

## Future integration

A later bridge implementation may attach behind the same handler/runtime path:

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager
RouteRuntimeManager -> RouteBridgeBoundary
RouteBridgeBoundary -> future NetworkBridge or future HardwareBridge
```

That later implementation must still keep the bridge as an adapter to the route
data plane, not as a second scheduler and not as a second EventBus.
