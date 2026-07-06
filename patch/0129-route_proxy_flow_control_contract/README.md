# 0129 — RouteProxy flow-control contract

Purpose: add pure immutable contracts for fast RouteProxy control around `/dev/shm` route zones.

Scope:

- Scheduler remains the orchestrator.
- RouteProxy is fast data-plane flow control, not an orchestrator.
- `/dev/shm` route zones are a multitask interface and future grid seam.
- EventBus receives observation facts/statistics, not payload commands.
- SQLContextStore remains durable authority.
- E5/OpenVINO remains embedding only behind adapter.
- Qdrant remains projection and recall only.

No runtime daemon, watcher, GitHub client, Qdrant client, OpenVINO runtime, PostgreSQL driver, socket, or kernel-loop edit is introduced.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_proxy_flow_control_contract.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_proxy_flow_control_0129_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
