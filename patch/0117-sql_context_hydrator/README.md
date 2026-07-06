# 0117 — SQLContextHydrator

This patch adds the read-side SQL hydration boundary above the 0116 `SQLContextStore`.

It introduces immutable hydration requests, bounded hydration policy, lightweight hydrated fragments, and a deterministic bundle that later reducers/specialists can consume.

The hydrator consumes an injected read-only SQL context store; it does not import PostgreSQL drivers, Qdrant, OpenVINO, LLM runtimes, sockets, Scheduler, Dispatcher, PolicyEngine, EventBus, or RouteRuntimeManager.

## Apply

```bash
python apply_patch_queue.py --patch 0117-sql_context_hydrator --dry-run
python apply_patch_queue.py --patch 0117-sql_context_hydrator --commit --push
```

## Validate

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_sql_context_hydrator.py
PYTHONPATH=src:. pytest -q tests/rules/test_sql_context_hydrator_0117_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
