# 0131 — Scheduler route handler minimal

Purpose: add a minimal handler/executor bridge that consumes Scheduler-owned route command data and writes frames through RouteProxyRuntime.

Scope:

- Scheduler remains the orchestrator.
- Handler is an executor bridge only.
- RouteProxyRuntime performs `/dev/shm` IO.
- EventBus receives observation-ready facts later, not payload commands.
- SQLContextStore remains durable authority.
- E5/OpenVINO and Qdrant are not touched.

No Scheduler.run(), Dispatcher, Queue, PolicyEngine, EventBus, OpenVINO, Qdrant, PostgreSQL, GitHub, daemon, watcher, socket, or network client is introduced.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests
PYTHONPATH=src:. pytest -q tests/runtime/test_scheduler_route_handler_minimal.py tests/rules/test_scheduler_route_handler_minimal_0131_rule.py
PYTHONPATH=src:. pytest -q tests/runtime tests/rules
```
