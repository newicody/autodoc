# 0116-sql_context_store_minimal

Adds the first minimal durable SQL context-store boundary.

Scope:

- Adds `src/context/sql_context_store.py` with immutable `SqlContextRecord`, a DB-API `DbApiSqlContextStore`, and a stdlib `SQLiteSqlContextStore` for tests.
- Documents the local production target: PostgreSQL 18 active on `fast_pool` at `/srv/autodoc/postgres/data`, with `data_pool` receiving ZFS snapshots/backups.
- Keeps Qdrant and OpenVINO as later adapters/projections, not context authority.
- Does not import psycopg, Qdrant, OpenVINO, LLM runtimes, sockets, or HTTP clients.
- Does not modify Scheduler, Dispatcher, PriorityQueue, PolicyEngine, EventBus, ControlProxy, or RouteRuntimeManager.

Apply after the context-base sequence:

```bash
python apply_patch_queue.py --patch 0113-context_variability_relock --dry-run
python apply_patch_queue.py --patch 0113-context_variability_relock --commit --push

python apply_patch_queue.py --patch 0114-r2-context_variation_core_contract --dry-run
python apply_patch_queue.py --patch 0114-r2-context_variation_core_contract --commit --push

python apply_patch_queue.py --patch 0115-context_exploration_planner --dry-run
python apply_patch_queue.py --patch 0115-context_exploration_planner --commit --push
```

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_sql_context_store_minimal.py
PYTHONPATH=src:. pytest -q tests/rules/test_sql_context_store_0116_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
