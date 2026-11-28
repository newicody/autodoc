# 0109 compatibility wrapper cleanup

0109 is a cleanup boundary after the 0101-0108 simplification locks.

It does not remove legacy functions yet. It marks the old ControlProxy Scheduler-facing helpers as **compatibility wrappers** and fixes the direction for future code:

```text
prepare_route_for_scheduler
handle_scheduler_route_request
```

These symbols remain valid for compatibility, but we do not extend them with new runtime logic.

```text
do not extend legacy wrappers
```

The replacement direction is:

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager
RouteRuntimeManager -> ControlFS + mmap/eventfd data plane
```

## Locked responsibilities

```text
No Scheduler.run() modification
Dispatcher = EventType -> Handler only
PolicyEngine = minimal admission before queue
PriorityQueue = deterministic execution order
Handler -> RouteRuntimeManager
Specialist branch owns business logic
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
No ControlProxyBus
No RouteBus
No VisualizationBus
No scheduler-like ControlProxy coordinator
```

## Why this exists

The previous phases created useful primitives, but two helper paths can be misunderstood as competing entry points:

```text
0085 prepare_route_for_scheduler
0086 handle_scheduler_route_request
0104 controlproxy_route_runtime_handler
0103 RouteRuntimeManager
```

0109 says which path wins without breaking existing imports:

```text
legacy helpers = compatibility wrappers
new runtime effects = thin Handler -> RouteRuntimeManager
```

A later patch can safely route the legacy symbols through the manager when the payload contracts are fully aligned.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0109 adds an explicit compatibility boundary and does not change kernel, policy, queue or dispatcher code.
live_path_status: cleanup
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
```
