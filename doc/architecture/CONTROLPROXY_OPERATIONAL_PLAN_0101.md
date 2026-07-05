# ControlProxy operational plan after 0101

0101 replaces the scheduler-like coordinator direction with a simpler roadmap.

## Locked roadmap

```text
0101 architecture simplification lock
0102 audit existing ControlProxy helpers and mark compatibility wrappers
0103 introduce RouteRuntimeManager
0104 slim ControlProxy handler to call RouteRuntimeManager
0105 clarify priority/admission as minimal kernel policy
0106 enforce EventBus versus data-plane separation
0107 rebuild root and individual architecture graphs after code simplification
```

## 0102 — audit existing paths

0102 should not add a new runtime capability. It should classify the current helpers.

```text
0085 prepare_route_for_scheduler = compatibility wrapper candidate
0086 handle_scheduler_route_request = compatibility wrapper candidate
0088 ControlProxySchedulerRouteRequestHandler = thin handler candidate
0091-r2 generation table = runtime primitive
0092 lifecycle = runtime primitive
0094 route generation lock = runtime primitive
0095 locked materializer = runtime primitive
0096 runtime placement = runtime primitive
0098 dispatch filter envelope = boundary filter primitive
```

## 0103 — RouteRuntimeManager

0103 should add a narrow runtime facade.

```text
RouteRuntimeManager.prepare_route(...)
RouteRuntimeManager.materialize_generation(...)
RouteRuntimeManager.activate_generation(...)
RouteRuntimeManager.mark_draining(...)
RouteRuntimeManager.mark_closed(...)
RouteRuntimeManager.cleanup_closed(...)
```

It composes primitives; it does not schedule work globally.

## 0104 — handler slimming

0104 should make the control path explicit.

```text
Scheduler.run()
-> Dispatcher.dispatch()
-> ControlProxySchedulerRouteRequestHandler.handle()
-> RouteRuntimeManager.prepare_route()
```

The handler remains an adapter. The runtime manager remains a runtime boundary. The specialist remains the business branch.

## 0105 — priority and admission

0105 should keep priorities simple.

```text
PolicyEngine = minimal admission gate before queue
PriorityQueue = deterministic ordering
Dispatcher = no priority mutation
ControlProxy = no global priority calculation
```

## 0106 — bus and data-plane separation

0106 should remove wording or code shape that suggests a second bus.

```text
EventBus = observation only
Context snapshot = context state
mmap/eventfd = data plane
RouteMessageJournal = replay/journal projection
Visualization adapter = reader of existing bus
```

## 0107 — graph rebuild

0107 should update the root graph and individual graph overlays after the code is simplified. The graph must show the implemented shape, not the intended future as if it were already wired.

```text
root graph
-> micro-kernel Scheduler path
-> Dispatcher boundary
-> Specialist branch
-> ControlProxy RouteRuntimeManager boundary
-> Context boundary
-> EventBus observation
-> mmap/eventfd data plane
```
