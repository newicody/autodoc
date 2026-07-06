# 0140 — Qdrant projection operator REST smoke

Purpose: execute the first live Qdrant projection smoke through existing repository contracts, without adding a new Qdrant adapter.

Scope:

- Extends `tools/run_qdrant_projection_live_smoke.py`.
- Reuses `src/inference/qdrant_projection_adapter.py` as the existing projection membrane.
- Uses the existing `QdrantProjectionExecutor` injection seam concept.
- Uses standard-library REST calls in the operator tool only.
- Keeps Scheduler, RouteProxy, PolicyEngine, Dispatcher, and context contracts outside Qdrant.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py tests/rules/test_qdrant_projection_operator_rest_smoke_0140_rule.py
```
