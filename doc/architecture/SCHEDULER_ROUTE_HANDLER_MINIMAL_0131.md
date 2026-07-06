# 0131 — Scheduler route handler minimal

SchedulerRouteHandler is an executor bridge, not an orchestrator.

0131 adds a minimal importable handler that consumes immutable Scheduler-owned command data and writes route frames through `RouteProxyRuntime`.  It does not modify Scheduler, Dispatcher, Queue, PolicyEngine, EventBus, OpenVINO, Qdrant, SQL, or GitHub code.

## Locked boundary

- Scheduler remains the orchestrator.
- SchedulerRouteHandler is an executor bridge, not an orchestrator.
- Do not modify Scheduler.run() in 0131.
- RouteProxyRuntime performs the /dev/shm IO.
- EventBus receives observation-ready facts, not payload commands.
- SQLContextStore remains durable authority.
- E5/OpenVINO and Qdrant are not touched by 0131.
- GitHub remains artifact exchange only.
- The handler may be called later by the real Scheduler/Dispatcher/Handler chain.

## Flow

```text
SchedulerRouteHandlerCommand
-> SchedulerRouteFrameRequest[]
-> RouteProxyRuntime.request_writer_permit()
-> RouteProxyRuntime.write_route_frame()
-> persisted route frame
-> observation-ready facts
```

The handler only executes route IO that the caller already decided to dispatch. It does not rank specialists, decide policy, resolve context, run embeddings, or publish to EventBus directly.

## Why this step matters

0130 made RouteProxyRuntime live. 0131 creates the first handler-shaped bridge that a Scheduler path can call without changing `Scheduler.run()`.

This is the shortest safe path toward:

```text
Scheduler command
-> handler
-> /dev/shm frame
-> fake specialist worker
-> opinion frame
-> collector
```

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: 0131 adds the first handler/executor membrane between Scheduler-owned command data and RouteProxyRuntime IO.
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
