# 0102 — ControlProxy existing paths audit

## Decision

0102 is audit and marking only.

The goal is to prevent another parallel architecture before 0103 introduces `RouteRuntimeManager`.

The locked command path remains:

```text
Component / Specialist
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> capability boundary
```

The route runtime path remains a data-plane boundary, not a command bus:

```text
ControlProxy handler
-> future RouteRuntimeManager
-> ControlFS
-> mmap/eventfd data plane
-> generation table / lifecycle / lock / placement
```

## Current path classification

### Micro-kernel boundaries

```text
Scheduler = loop, time, queue submission, priority execution boundary
PolicyEngine = minimal admission gate before queue
PriorityQueue = sole deterministic ordering mechanism
Dispatcher = EventType -> Handler only
Handler = thin adapter from Event/Request to one capability boundary
Specialist branch = business logic, reasoning, transformation, strategy
EventBus = observation only
```

These boundaries are not ControlProxy responsibilities.

### ControlProxy Scheduler-facing compatibility path

The Scheduler-facing helpers remain valid as compatibility wrapper candidates until 0104 slims them around `RouteRuntimeManager`.

```text
prepare_route_for_scheduler = compatibility wrapper candidate
handle_scheduler_route_request = compatibility wrapper candidate
ControlProxySchedulerRouteRequestHandler = thin handler candidate
```

They must not become a second Scheduler. They must converge toward:

```text
Dispatcher
-> ControlProxySchedulerRouteRequestHandler
-> RouteRuntimeManager.prepare_route(...)
```

### Route runtime primitives

The following phases are runtime primitives. They are useful, but they should be composed by one future runtime manager rather than by new ad-hoc coordinators.

```text
mmap fixed-slot route = data plane primitive
route notifier eventfd/pipe = data plane notification primitive
route lease state = route-client lifecycle primitive
active route materializer = existing materialization primitive
generation table g2/g3 = generation-state primitive
route generation lifecycle = candidate/active/draining/closed primitive
route generation lock = inter-process guard primitive
locked materializer = critical-section composition primitive
runtime placement file/dev_shm = explicit placement primitive
route dispatch filter envelope = boundary filter primitive, not security authority
```

### Observation and journal paths

```text
EventBus = observation only
existing bus visualization adapter = reader of the existing bus
RouteMessageJournal = journal/replay projection of drained route messages
Recorder = future higher-level replay/recording projection
```

`RouteMessageJournal` is not a second EventBus and not the final Recorder. It is a data-plane journal that can feed a Recorder later.

### Context and search paths

```text
TaskContext / ContextGate = context authority
GlobalContextSnapshot = kernel-level context view
Qdrant = projection/search index only
InferenceContext = specialist-facing reasoning context
```

Qdrant must not become the context authority. ContextGate and TaskContext remain the authority. Qdrant remains projection and search.

### Future bridge paths

```text
NetworkBridge = future external bridge, not current command path
HardwareBridge = future external bridge, not current command path
ClusterFabric = future distributed placement fabric, not current route manager
```

They remain out of scope until the local route runtime is coherent.

## Duplication risk register

| Area | Duplicate-looking pieces | Risk | Decision before 0103 |
| --- | --- | --- | --- |
| Scheduler / ControlProxy | Scheduler loop and ControlProxy route lifecycle | ControlProxy becomes scheduler-like | ControlProxy remains runtime boundary only |
| PolicyEngine / route dispatch filter | admission policy and filter envelope | two security authorities | PolicyEngine admits; filter envelope guards dispatch shape |
| Dispatcher / specialist | EventType routing and business translation | Dispatcher starts doing specialist work | Dispatcher remains EventType -> Handler only |
| Handler / runtime manager | handler adaptation and route runtime operations | handler becomes runtime brain | handler becomes thin adapter in 0104 |
| EventBus / mmap-eventfd | observation bus and route data plane | a second bus appears | mmap/eventfd is data plane, not EventBus |
| Recorder / RouteMessageJournal | event replay and route-message journal | two recorders | RouteMessageJournal is low-level projection; Recorder is later aggregation |
| ContextGate / Qdrant | context authority and vector projection | search index becomes authority | ContextGate/TaskContext remain authority |
| lease state / generation lifecycle | client lease and segment generation state | two state machines collapse into confusion | keep separate until 0103 maps them explicitly |
| active materializer / locked materializer | existing materialization and lock-wrapped generation | duplicated materializers | RouteRuntimeManager chooses one composed path |
| runtime placement / ControlFS | placement root and state root | hidden /dev/shm assumption | placement is explicit; ControlFS records state |

## 0103 entry criteria

0103 may add code only if it preserves these rules:

```text
RouteRuntimeManager planned next.
RouteRuntimeManager composes runtime primitives.
RouteRuntimeManager does not schedule global work.
RouteRuntimeManager does not calculate global priority.
RouteRuntimeManager does not create a bus.
RouteRuntimeManager does not become PolicyEngine.
RouteRuntimeManager does not replace Dispatcher.
```

## 0104 entry criteria

0104 may slim the handler only after 0103 exists.

```text
ControlProxySchedulerRouteRequestHandler remains thin.
prepare_route_for_scheduler remains compatibility wrapper or is explicitly deprecated.
handle_scheduler_route_request remains compatibility wrapper or is explicitly deprecated.
Dispatcher still resolves EventType -> Handler only.
```

## Non-goals

```text
No CLI.
No daemon/service/OpenRC.
No resident watcher.
No runtime code in this phase.
No Scheduler.run() modification.
No PriorityQueue modification.
No Dispatcher implementation modification.
No PolicyEngine implementation modification.
No EventBus implementation modification.
No new bus.
No ControlProxyRouteCoordinator scheduler-like.
No RouteRuntimeManager implementation yet.
No Qdrant / LLM / OpenVINO / NetworkBridge / HardwareBridge path.
```
