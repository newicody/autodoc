# 0137 — local vector-indexing test readiness

Adds a read-only readiness gate before the first local vector-indexing smoke test.

Scope:

- inventory existing Scheduler/RouteProxy/OpenVINO/Qdrant/SQL surfaces
- list steps before the first real smoke test
- prevent creation of parallel runtime/adapter/orchestrator wheels

No runtime, adapter, daemon, network client, Scheduler edit, OpenVINO launch, Qdrant launch, SQL connection, EventBus call, or `/dev/shm` IO is added.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_local_vector_indexing_smoke_readiness_0137.py tests/rules/test_local_vector_indexing_smoke_readiness_0137_rule.py
```
