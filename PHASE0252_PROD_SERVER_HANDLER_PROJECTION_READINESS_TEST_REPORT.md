# Phase 0252 test report - handler projection readiness

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_handler_projection_readiness_0252.py
python -m pytest -q tests/tools/test_run_prod_server_handler_projection_readiness_0252.py
python -m pytest -q tests/rules/test_prod_server_handler_projection_readiness_0252_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_handler_projection_readiness_0252.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_handler_projection_readiness_0252.py --format summary
```

## Boundary

This patch derives projection readiness only. It does not execute SQL, run
OpenVINO, call Qdrant, write Qdrant points, dispatch handlers, call
Scheduler.run, publish events, call GitHub, or add non-stdlib dependencies.
