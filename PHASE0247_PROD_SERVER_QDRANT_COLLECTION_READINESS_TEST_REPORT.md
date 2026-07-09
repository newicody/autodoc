# Phase 0247 test report - Qdrant collection readiness

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_prod_server_qdrant_collection_readiness_0247.py
python -m pytest -q tests/tools/test_run_prod_server_qdrant_collection_readiness_0247.py
python -m pytest -q tests/rules/test_prod_server_qdrant_collection_readiness_0247_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_prod_server_qdrant_collection_readiness_0247.py --check-only --format summary
PYTHONPATH=src:. python tools/run_prod_server_qdrant_collection_readiness_0247.py --format summary
```

## Boundary

This patch checks readiness only. It does not call Qdrant, create collections,
upsert points, run OpenVINO inference, write PostgreSQL, publish events, call
GitHub, or add non-stdlib dependencies.
