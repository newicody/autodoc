# 0133 — Existing scheduler route handler integration

0133 extends existing scheduler_route_handler_minimal.py.

This phase is deliberately not a new runtime, not a new worker, and not a fake specialist.  The 0132 audit decision is `reuse_or_extend_existing`, so 0133 modifies the existing Scheduler route handler surface and reuses RouteProxyRuntime.

## Locked decision

- 0133 extends existing scheduler_route_handler_minimal.py.
- Do not create fake_specialist_worker_minimal.py in 0133.
- Do not create a new route handler or runtime wheel when audited surfaces exist.
- Scheduler remains the orchestrator.
- RouteProxyRuntime remains the IO executor.
- Scheduler.run() is not modified.
- EventBus receives observation-ready facts only.
- OpenVINO and Qdrant remain out of this handler patch.
- 0132 audit decision: reuse_or_extend_existing.

## Reused surfaces

The integration decision records these existing surfaces as reusable/extendable:

```text
src/runtime/scheduler_route_handler_minimal.py
src/runtime/route_proxy_runtime_minimal.py
src/runtime/controlproxy_scheduler_handler.py
src/runtime/controlproxy_route_runtime_handler.py
src/runtime/route_dev_shm_runtime.py
src/runtime/route_runtime_manager.py
src/runtime/scheduler_route_adapter.py
src/runtime/scheduler_route_handshake.py
```

The patch adds readback helpers to the existing handler so a caller can prove that a Scheduler-dispatched frame was written through RouteProxyRuntime and can be read back from the same runtime state.

## Why this matters

The next prototype step needs a path that is real enough to support worker/specialist consumption, but adding another fake worker would duplicate existing runtime surfaces.  0133 therefore strengthens the existing handler instead of creating a parallel wheel.

## Boundary

```text
Scheduler-owned command data
-> existing scheduler_route_handler_minimal.py
-> existing RouteProxyRuntime
-> /dev/shm or explicit test root
-> readback frames for later consumers
-> observation-ready facts
```

No OpenVINO, Qdrant, PostgreSQL, GitHub client, EventBus runtime client, daemon, watcher, or Scheduler loop mutation is introduced.
