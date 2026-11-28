# 0105 — Scheduler priority and admission lock

## Decision

This phase locks the simplified priority/admission model before any further
ControlProxy runtime work.

The invariant is:

```text
Scheduler = loop + time + queue + priority
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution ordering
Dispatcher = EventType -> Handler only
Handler = thin adapter
Specialist branch = business reasoning / transformation / strategy
ControlProxy / RouteRuntimeManager = route runtime transport over ControlFS + mmap/eventfd
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
```

## Priority ownership

PriorityQueue is the only deterministic execution ordering mechanism.

Priority is a scheduler-facing value. It may be carried by an event or by a
typed command before the event is emitted. It is not recomputed by the
Dispatcher and it is not recomputed by ControlProxy / RouteRuntimeManager.

Current rule:

```text
Event priority -> PolicyEngine admission -> PriorityQueue ordering -> Scheduler.run()
```

Allowed future extension:

```text
EventClassPolicy + bounded GlobalContextSnapshot -> explicit priority value
```

That extension must stay before enqueue and must remain deterministic. It must
not be hidden inside the Dispatcher, ControlProxy, EventBus, route mmap/eventfd,
or the visualization path. Future priority policy must not be hidden inside the Dispatcher, ControlProxy, EventBus.

## Admission ownership

PolicyEngine is minimal admission before queue.

The current PolicyEngine is kept because it gives the kernel a deterministic
admission gate before scheduling. It may validate source, destination, priority
range, reserved event types, declared backend permissions, and similar kernel
admission facts.

PolicyEngine must not become a business engine. It must not choose a route
mmap generation, a runtime placement, a specialist strategy, a Qdrant query, an
OpenVINO backend, or a long-running exploration plan.

## Dispatcher ownership

Dispatcher is EventType -> Handler only.

Dispatcher keeps Scheduler.run() thin by resolving the handler and by keeping
reply resolution at the kernel boundary. It does not compute priority, it does
not decide admission, and it does not implement ControlProxy route runtime
logic.

## ControlProxy / RouteRuntimeManager ownership

ControlProxy / RouteRuntimeManager does not compute global priorities.

ControlProxy / RouteRuntimeManager does not decide policy/zone admission.

It may reject malformed route-runtime input at its boundary, for example a
missing route id or an absent policy_decision_id on a scheduler-originated route
request. That rejection is a local boundary guard, not a new scheduling policy
and not a second security authority.

Its runtime scope is:

```text
ControlFS state
mmap/eventfd data plane
route generation table
generation lifecycle
file/dev_shm placement
inter-process generation lock
RouteMessage journal input
```

## Bus separation

EventBus is observation only.

Route mmap/eventfd is data plane, not EventBus.

No ControlProxyBus, RouteBus, or VisualizationBus should be introduced for this
path. Visualization adapters must read the existing EventBus and existing
context snapshots. Route transports may emit observable facts later, but they
must not become a command bus.

## Specialist branch

The specialist branch owns business reasoning and transformation.

A specialist may later produce explicit priority hints or typed commands, but
those hints must enter the normal kernel path:

```text
Command dataclass -> Scheduler.emit() -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
```

The specialist must not bypass the Scheduler by calling RouteRuntimeManager or
other backends directly for durable system behavior.

## Code impact

This phase is an architecture/rules lock only.

It does not modify Scheduler.run(), Dispatcher, PriorityQueue, PolicyEngine,
ControlProxy runtime code, handlers, EventBus, or Component.tick/yield/reply.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: this phase restates and narrows existing code_rule.md invariants without changing the global rule contract.
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
