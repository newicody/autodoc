# Phase 0262 test report - Scheduler-managed embedding to Qdrant projection usage

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_managed_embedding_qdrant_projection_usage_0262.py
python -m pytest -q tests/tools/test_run_scheduler_managed_embedding_qdrant_projection_0262.py
python -m pytest -q tests/rules/test_scheduler_managed_embedding_qdrant_projection_usage_0262_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Dry-run smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_embedding_qdrant_projection_0262.py --embedding-report .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json --output .var/reports/scheduler_managed_embedding_qdrant_projection_0262.json --format summary
```

## Demo execute smoke

```text
PYTHONPATH=src:. python tools/run_scheduler_managed_embedding_qdrant_projection_0262.py --embedding-report .var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json --execute --policy-decision-id policy:0262:demo --demo-qdrant --output .var/reports/scheduler_managed_embedding_qdrant_projection_0262.json --format summary
```

## Boundary

Scheduler uses Qdrant. Scheduler does not start Qdrant. SQL remains the durable
authority.
