# Phase 0263 test report - Scheduler-managed Qdrant recall to SQL rehydrate usage

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py
python -m pytest -q tests/tools/test_run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py
python -m pytest -q tests/rules/test_scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Dry-run smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py --embedding-report .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json --projection-report .var/reports/scheduler_managed_embedding_qdrant_projection_0262.json --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --output .var/reports/scheduler_managed_qdrant_recall_sql_rehydrate_0263.json --format summary
```

## Demo execute smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py --embedding-report .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json --projection-report .var/reports/scheduler_managed_embedding_qdrant_projection_0262.json --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --execute --policy-decision-id policy:0263:demo --demo-qdrant --output .var/reports/scheduler_managed_qdrant_recall_sql_rehydrate_0263.json --format summary
```

## Boundary

Scheduler uses Qdrant recall. Scheduler does not start Qdrant. SQL remains the
durable authority.
