# Phase 0261 test report - Scheduler-managed sql_ref to OpenVINO embedding usage

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_managed_sql_ref_openvino_embedding_usage_0261.py
python -m pytest -q tests/tools/test_run_scheduler_managed_sql_ref_openvino_embedding_0261.py
python -m pytest -q tests/rules/test_scheduler_managed_sql_ref_openvino_embedding_usage_0261_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Dry-run smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --binding-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json --output .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json --format summary
```

## Real OpenVINO execute smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --binding-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json --execute --policy-decision-id policy:0261:demo --format summary
```

## Demo execute smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py --db-path .var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3 --binding-report .var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json --execute --policy-decision-id policy:0261:demo --demo-embedding --format summary
```

## Boundary

Scheduler uses OpenVINO/E5. Scheduler does not start OpenVINO. Qdrant is not
involved in 0261.
