# Phase 0260 test report - Scheduler-managed DbApiSqlContextStore binding

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_managed_db_api_sql_context_store_binding_0260.py
python -m pytest -q tests/tools/test_bind_scheduler_managed_db_api_sql_context_store_0260.py
python -m pytest -q tests/rules/test_scheduler_managed_db_api_sql_context_store_binding_0260_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/bind_scheduler_managed_db_api_sql_context_store_0260.py --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json --output .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json --format summary
```

## Execute smoke

```text
PYTHONPATH=src:. python tools/bind_scheduler_managed_db_api_sql_context_store_0260.py --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json --execute --policy-decision-id policy:0260:demo --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --format summary
```

## Boundary

Scheduler uses an existing DbApiSqlContextStore object.  It does not start
PostgreSQL, create a SQL store, create a RuntimeManager, modify Scheduler.run,
call Qdrant, run OpenVINO, call GitHub, or publish EventBus commands.

## 0260-r2 expected fix

Strict `DbApiSqlContextStore` class detection and file-path candidate loading should make the focused context/tool tests pass against temporary roots and prevent selecting the 0260 binder module itself.
