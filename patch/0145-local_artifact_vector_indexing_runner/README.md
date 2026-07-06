# 0145 — Local artifact vector indexing runner

Purpose: wrap the validated Scheduler/RouteProxy/vector smoke in a local artifact input/result envelope.

This patch adds one operator tool:

- `tools/run_local_artifact_vector_indexing_runner.py`

It reuses existing surfaces:

- `tools/run_scheduler_vector_indexing_smoke.py`
- `src/runtime/scheduler_route_handler_minimal.py`
- `src/runtime/route_proxy_runtime_minimal.py`
- `tools/run_local_vector_indexing_live_smoke.py`
- `tools/embed_e5.py --format json --full-vector`
- `tools/run_qdrant_projection_live_smoke.py --vector-json`

It does not create a new orchestrator, Scheduler runner, OpenVINO adapter, or Qdrant adapter.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_local_artifact_vector_indexing_runner_0145.py tests/rules/test_local_artifact_vector_indexing_runner_0145_rule.py
```
