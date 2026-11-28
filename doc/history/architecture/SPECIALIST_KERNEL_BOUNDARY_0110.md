# 0110 — Specialist kernel boundary

0110 locks the specialist integration direction after the ControlProxy simplification.

The specialist branch owns business logic, reasoning and transformation. It does not own the Scheduler, EventBus, RouteRuntimeManager, ControlFS or mmap/eventfd data plane.

## Locked path

```text
SpecialistKernelCommand -> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
```

When a specialist command eventually needs a route runtime effect, the path continues:

```text
Handler -> RouteRuntimeManager
-> ControlFS + Route mmap/eventfd data plane
```

No direct Specialist -> RouteRuntimeManager call is allowed.

## Responsibilities

```text
Specialist branch owns business logic.
Scheduler = loop + time + queue + priority.
PolicyEngine = minimal admission before queue.
PriorityQueue = deterministic execution order.
Dispatcher = EventType -> Handler only.
Handler = thin adapter.
RouteRuntimeManager owns route runtime work.
EventBus = observation only.
Route mmap/eventfd = data plane, not EventBus.
```

## Forbidden directions

```text
No direct Specialist -> RouteRuntimeManager call
No direct Specialist -> ControlFS call
No direct Specialist -> mmap/eventfd data plane call
No EventBus creation
No ControlProxyBus
No RouteBus
No VisualizationBus
No scheduler-like ControlProxy coordinator
No Scheduler.run() modification
```

## Why this is not another coordinator

`SpecialistKernelCommand` is not an Event, not a Scheduler and not a runtime manager. It is a stable command envelope a future adapter may wrap into an Event before calling `Scheduler.emit()`.

This keeps churn in the specialist leaf while the stable boundary remains the kernel path.

## Relation to RouteRuntimeManager

`RouteRuntimeManager` remains below the Handler boundary. The specialist can request a route-related capability, but the route runtime effect is performed only after admission, queuing, dispatch and handler adaptation.

## Report against `code_rule.md`

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0110 applies the existing durable-capability path and adds no new programming exception.
live_path_status: transition
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
```
