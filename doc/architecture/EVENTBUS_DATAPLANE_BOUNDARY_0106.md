# 0106 — EventBus / data plane boundary lock

0106 locks the boundary between the kernel observation channel and the local
route runtime transport.

This patch is intentionally documentation and rule tests only. It does not add
runtime code because the architecture decision must be stable before the next
implementation phase.

## Locked responsibilities

```text
Scheduler = cooperative loop + time + queue + priority
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution order
Dispatcher = EventType -> Handler only
Handler = thin adapter
Specialist branch = business logic / reasoning / transformation
ControlProxy / RouteRuntimeManager = route runtime transport, ControlFS, mmap/eventfd data plane
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
RouteMessageJournal = drained route message journal, not EventBus
Visualization adapter = existing EventBus/context reader, not bus owner
```

## EventBus

The EventBus is the kernel observation path. It carries facts for telemetry,
recording, replay and visualization readers.

It must not command execution. The deterministic command path remains:

```text
Scheduler.emit() -> PolicyEngine.decide() -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
```

The EventBus may receive derived observations produced by handlers or runtime
boundaries, but those observations do not become commands.

## Data plane

The route runtime data plane is the local high-throughput path used by
ControlProxy / RouteRuntimeManager.

It is made of explicit runtime primitives:

```text
mmap fixed-slot route
route notifier / eventfd or fallback pipe
route lease state
route generation table g2/g3
route lifecycle candidate -> active -> draining -> closed
route runtime placement file/dev_shm
RouteMessageJournal for drained messages
```

The data plane is not a bus. It does not dispatch application commands and it
must not replace EventBus.

## Forbidden confusions

The architecture rejects these shortcuts:

```text
No ControlProxyBus
No RouteBus
No VisualizationBus
No bus created by ControlProxy
No bus created by RouteRuntimeManager
No bus owned by visualization adapters
No mmap/eventfd command bus
No EventBus as command path
No Dispatcher business logic
No ControlProxy global priority management
```

## Allowed relation

The only allowed relation is observational:

```text
RouteRuntimeManager -> mmap/eventfd data plane -> drained RouteMessage -> RouteMessageJournal
RouteRuntimeManager -> optional observable facts -> existing EventBus
Visualization adapter -> reads existing EventBus/context snapshot
```

This means a route message can be recorded, summarized or projected into a
fact, but it does not become a second EventBus.

## Impact on next phases

0107 must update the root and individual architecture graphs so the runtime
subgraph shows:

```text
Scheduler -> Dispatcher -> Handler -> RouteRuntimeManager
RouteRuntimeManager -> ControlFS
RouteRuntimeManager -> mmap/eventfd data plane
RouteRuntimeManager -> RouteMessageJournal
EventBus -> observation side path only
ContextGate -> context authority
Qdrant -> projection/search only
```

0108 and later runtime work must keep this vocabulary. Any code that introduces
`ControlProxyBus`, `RouteBus`, a visualization-owned bus, or mmap/eventfd as a
command bus is a direction error.
