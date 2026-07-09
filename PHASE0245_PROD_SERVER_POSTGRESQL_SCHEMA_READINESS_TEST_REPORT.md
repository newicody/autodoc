# Phase 0245 test report - PostgreSQL schema readiness

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_postgresql_schema_readiness_0245.py
python -m pytest -q tests/tools/test_run_prod_server_postgresql_schema_readiness_0245.py
python -m pytest -q tests/rules/test_prod_server_postgresql_schema_readiness_0245_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_postgresql_schema_readiness_0245.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_postgresql_schema_readiness_0245.py --format summary
```

## Boundary

This patch checks readiness only. It does not connect to PostgreSQL, execute SQL,
write PostgreSQL, start OpenRC, create Scheduler/EventBus, publish events, call
GitHub, create Qdrant collections, or add non-stdlib dependencies.
