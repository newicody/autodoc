# Phase 0240 test report - production server initial configuration requirements

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_initial_config_requirements_0240.py
python -m pytest -q tests/tools/test_run_prod_server_initial_config_requirements_0240.py
python -m pytest -q tests/rules/test_prod_server_initial_config_requirements_0240_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_initial_config_requirements_0240.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_initial_config_requirements_0240.py --format summary
```

## Boundary

This patch is requirements-only. It does not start OpenRC, create
Scheduler/EventBus, start threads, publish events, call GitHub, publish to
GitHub, execute PostgreSQL DDL/DML, create Qdrant collections, or add non-stdlib
dependencies.
