# 0108 — ControlProxy route runtime live path

## Decision

0108 validates the simplified ControlProxy direction with a small **walking skeleton**.
It does not add a new runtime coordinator and it does not change the kernel loop.
The scenario proves the durable slice after Dispatcher has selected the thin
ControlProxy handler:

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager
RouteRuntimeManager -> ControlFS + mmap/eventfd data plane
```

## Scope

The test traverses:

```text
ControlProxySchedulerRouteRequestHandler
-> build_controlproxy_route_runtime_request_handler(manager)
-> RouteRuntimeManager.handle_prepare_decision()
-> locked generation materialization
-> ControlFS generation table
-> mmap route ring.bin
-> lifecycle active/draining/closed
-> closed-generation cleanup
```

It materializes g1, activates g1, materializes g2 with different sizing, then
drains/closes/cleans g1 while g2 remains present. This confirms that g2/g3 style
updates are new generations and not live mmap resize.

## Boundary lock

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- Dispatcher = EventType -> Handler only.
- PolicyEngine = minimal admission before queue.
- PriorityQueue = deterministic execution order.
- Handler -> RouteRuntimeManager.
- RouteRuntimeManager performs route runtime work only.
- Specialist branch owns business logic.
- EventBus = observation only.
- Route mmap/eventfd = data plane, not EventBus.
- ControlFS + mmap/eventfd data plane is not a command bus.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.

## What this is not

0108 is not a full Scheduler.run() integration test. That would require a stable
registered handler table and kernel event construction across the complete
micro-kernel. This phase is intentionally narrower: it validates the live runtime
slice that begins once Dispatcher has selected the handler.

The result is still useful because it prevents the previous drift: no
scheduler-like ControlProxy coordinator, no second bus, and no hidden priority or
policy decision inside ControlProxy.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0108 follows the existing micro-kernel path and adds no new programming rule.
live_path_status: green
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
