# Phase 0244 test report - OpenRC launcher surface

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_openrc_launcher_surface_0244.py
python -m pytest -q tests/tools/test_run_prod_server_openrc_launcher_surface_0244.py
python -m pytest -q tests/rules/test_prod_server_openrc_launcher_surface_0244_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_openrc_launcher_surface_0244.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_openrc_launcher_surface_0244.py --format summary
```

## Boundary

This patch validates the local OpenRC service surface only. It does not install
OpenRC files, call OpenRC commands, start the launcher, create Scheduler/EventBus,
start threads, publish events, call GitHub, execute PostgreSQL DDL/DML, create
Qdrant collections, or add non-stdlib dependencies.
