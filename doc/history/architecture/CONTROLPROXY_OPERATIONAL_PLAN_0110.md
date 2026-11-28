# ControlProxy operational plan — 0110

0110 introduces the specialist-side command boundary without changing runtime wiring.

## Decision

```text
Specialist branch owns business logic.
ControlProxy / RouteRuntimeManager owns route runtime work.
They meet only through the kernel path.
```

## Current locked path

```text
SpecialistKernelCommand -> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> RouteRuntimeManager when route runtime work is required
```

## Scope of 0110

```text
Add a typed specialist command envelope.
Add a boundary plan proving the next boundary is Scheduler.emit().
Keep route runtime effects behind Handler -> RouteRuntimeManager.
Document and test that there is No direct Specialist -> RouteRuntimeManager call.
```

## Out of scope

```text
No CLI
No OpenRC service and no resident daemon
No watcher
No Scheduler.run() modification
No Dispatcher, PriorityQueue, PolicyEngine or EventBus modification
No new EventType
No EventBus creation
No ControlProxyBus
No RouteBus
No VisualizationBus
No direct runtime effect from the specialist
Route mmap/eventfd = data plane, not EventBus
EventBus = observation only
PolicyEngine = minimal admission before queue
Dispatcher = EventType -> Handler only
```

## Next steps

```text
0111: add a Scheduler-facing Event adapter for SpecialistKernelCommand only if an existing EventType boundary is selected explicitly.
0112: add a small specialist walking-skeleton scenario after the EventType/handler boundary is chosen.
0113: only then consider deprecating old ControlProxy compatibility wrappers.
```
