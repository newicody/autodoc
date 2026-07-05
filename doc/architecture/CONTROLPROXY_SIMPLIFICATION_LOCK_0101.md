# 0101 — ControlProxy simplification lock

## Decision

0101 locks the architecture before more ControlProxy code is added.

The current direction is simplified to one micro-kernel command path and one runtime data plane.

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

The route runtime path is not a second scheduler and not a second bus.

```text
ControlProxy / RouteRuntimeManager
-> ControlFS state
-> mmap/shm route segments
-> eventfd notifier
-> generation table
-> route lifecycle
```

## Locked responsibilities

```text
Scheduler = loop, time, queue, and priority orchestration.
PolicyEngine = minimal admission gate before the queue.
PriorityQueue = the only deterministic execution ordering mechanism.
Dispatcher = EventType -> Handler only.
Handler = thin adapter from kernel event/request to capability boundary.
Specialist branch = business logic, reasoning, transformation, strategy.
ControlProxy / RouteRuntimeManager = runtime transport for route/mmap/controlfs.
EventBus = observation only.
Route mmap/eventfd = data plane, not EventBus.
ContextEngine / ContextGate = context authority.
Qdrant = projection/search, not context authority.
```

## Explicit simplifications

ControlProxy must not own global priority calculation.  ControlProxy must not create another bus.  ControlProxy must not become a Scheduler-bis.  ControlProxy must not decide business policy.  ControlProxy can reject malformed or incomplete route envelopes only as a boundary filter.

PolicyEngine remains useful, but only as an admission gate. It does not choose route generations, mmap placement, specialist behavior, or backend strategy.

Dispatcher remains useful, but only as a micro-kernel boundary. It routes by event type to a handler, publishes observation through the existing EventBus when the existing kernel does that, and resolves replies according to the existing contract. It does not perform business translation, zone strategy, priority mutation, or runtime materialization.

The branch specialist remains the place for business interpretation and transformation. A handler may adapt a kernel event into a specialist call, but the Dispatcher does not become that specialist and ControlProxy does not replace that specialist.

## Bus decision

There is one kernel observation EventBus. The existing EventBus remains the observation path. A visualization adapter may read an existing bus subscription, but it must not create a visualization bus or a route bus.

The route mmap/eventfd mechanism is a runtime data plane. It may produce observable facts through the existing EventBus or journal, but it is not EventBus and is not a command bus.

## Priority decision

Priorities stay simple for this phase.

```text
Event priority -> PriorityQueue -> Scheduler.run() ordering
```

A future explicit policy may derive a priority hint from event type, source, and a bounded GlobalContextSnapshot, but that is not implemented here. ControlProxy does not calculate global priority, and Dispatcher does not mutate priority.

## Direction for the next code phase

The previously proposed scheduler-like ControlProxyRouteCoordinator is not accepted as the next direction.

The next runtime code phase should introduce a narrow `RouteRuntimeManager`, not a scheduler-like coordinator.

```text
Dispatcher -> ControlProxy handler -> RouteRuntimeManager
```

`RouteRuntimeManager` may compose existing route-generation, lock, placement, lifecycle, mmap, notifier, and journal primitives. It must remain behind the handler and must not touch Scheduler.run(), PriorityQueue, Dispatcher internals, PolicyEngine semantics, EventBus ownership, specialist logic, Qdrant, LLM, or OpenVINO.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0101 locks responsibilities already required by code_rule.md instead of expanding the rule.
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
search_commands_bounded: n/a
```
