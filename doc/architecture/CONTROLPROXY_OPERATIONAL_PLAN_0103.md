# ControlProxy operational plan — 0103

0103 implements the first code step after the simplification lock.

## Current decision

```text
Do not apply a scheduler-like ControlProxyRouteCoordinator.
Use RouteRuntimeManager as a strict runtime facade.
```

## Path after 0103

```text
Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> ControlProxy route Handler
-> RouteRuntimeManager
-> ControlFS + mmap/eventfd data plane
```

## 0103 scope

```text
RouteRuntimeManager materializes route generations under lock.
RouteRuntimeManager runs lifecycle transitions.
RouteRuntimeManager cleans only closed generations.
RouteRuntimeManager reads the generation table.
```

## Out of scope

```text
No CLI
No OpenRC service and no resident daemon
No watcher
No Scheduler.run() modification
No global priority management
No policy decision and no zone authority in ControlProxy
No EventBus creation and no bus duplication
Route mmap/eventfd is a data plane, not EventBus
EventBus remains observation only
Dispatcher remains EventType -> Handler only
PolicyEngine remains minimal admission before queue
Specialist branch owns business logic
```

## Next steps

```text
0104: slim the ControlProxy scheduler-facing handler so it delegates to RouteRuntimeManager.
0105: clarify priority/admission boundaries without adding dynamic scheduling.
0106: audit EventBus vs data plane vocabulary and remove any bus-duplication wording.
0107: regenerate root-attached graph views after the code path is slimmed.
```
