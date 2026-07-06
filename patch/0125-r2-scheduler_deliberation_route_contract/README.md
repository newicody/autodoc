# 0125-r2 — Scheduler deliberation route contract

This patch replaces the rejected local server orchestrator direction with Scheduler-owned deliberation route contracts.

It locks:

- Scheduler is the deliberation orchestrator.
- /dev/shm route frames are a multitask data-plane interface for local workers and a future grid.
- EventBus observes facts, statistics, and paths, not payload commands.
- GitHub exchanges artifacts only: artifact in and final artifact out.
- E5/OpenVINO is embedding only behind adapter, not decision maker.
- SQLContextStore remains durable context authority.

No Scheduler.run(), Dispatcher, Queue, PolicyEngine, EventBus, RouteRuntimeManager, GitHub client, HTTP/socket client, Qdrant client, OpenVINO runtime, PostgreSQL driver, LLM SDK, service, daemon, watcher, or VisPy renderer is modified.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_scheduler_deliberation_route_contract.py
PYTHONPATH=src:. pytest -q tests/rules/test_scheduler_deliberation_route_contract_0125_r2_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
