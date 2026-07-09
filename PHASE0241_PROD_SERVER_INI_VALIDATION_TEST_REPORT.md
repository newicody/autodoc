# Phase 0241 test report - production server INI validation

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_ini_validation_0241.py
python -m pytest -q tests/tools/test_run_prod_server_ini_validation_0241.py
python -m pytest -q tests/rules/test_prod_server_ini_validation_0241_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_ini_validation_0241.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_ini_validation_0241.py --format summary
```

## Boundary

This patch validates a local INI file only. It does not start OpenRC, create
Scheduler/EventBus, publish events, call GitHub, publish to GitHub, execute
PostgreSQL DDL/DML, create Qdrant collections, or add non-stdlib dependencies.
