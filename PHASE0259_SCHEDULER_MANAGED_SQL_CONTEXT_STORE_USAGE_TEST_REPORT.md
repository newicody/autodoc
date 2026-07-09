# Phase 0259 test report - Scheduler-managed SQLContextStore usage

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_managed_sql_context_store_usage_0259.py
python -m pytest -q tests/tools/test_build_scheduler_managed_sql_context_store_usage_0259.py
python -m pytest -q tests/rules/test_scheduler_managed_sql_context_store_usage_0259_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/build_scheduler_managed_sql_context_store_usage_0259.py --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json --output .var/reports/scheduler_managed_sql_context_store_usage_0259.json --format summary
```

## Execute smoke with smoke-only existing store

```text
PYTHONPATH=src:. python tools/build_scheduler_managed_sql_context_store_usage_0259.py --bootstrap .var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json --execute --policy-decision-id policy:0259:demo --demo-existing-store --format summary
```

## Boundary

Scheduler uses an existing SQLContextStore object.  It does not start
PostgreSQL, create a SQL store, create a RuntimeManager, modify Scheduler.run,
call Qdrant, run OpenVINO, call GitHub, or publish EventBus commands.
