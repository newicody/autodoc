# 0144 — scheduler vector indexing result frame

Purpose: after the strict Scheduler/RouteProxy -> local vector indexing smoke succeeds, write a `vector_indexing_result` frame back through the existing Scheduler route handler and existing RouteProxyRuntime.

Scope:

- Extend existing `tools/run_scheduler_vector_indexing_smoke.py`.
- Extend existing `src/runtime/scheduler_route_handler_minimal.py` with the locked `vector_indexing_result` frame kind.
- Reuse `src/runtime/route_proxy_runtime_minimal.py` for frame IO.
- Reuse `tools/run_local_vector_indexing_live_smoke.py` for OpenVINO/E5 + Qdrant execution.
- Do not create a result worker, daemon, orchestrator, or backend adapter.
- Do not modify `Scheduler.run()`.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_scheduler_vector_indexing_result_frame_0144.py tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py
PYTHONPATH=src:. pytest -q tests/tools/test_scheduler_vector_indexing_smoke_0143.py tests/tools/test_scheduler_vector_indexing_result_frame_0144.py tests/rules/test_scheduler_vector_indexing_smoke_0143_rule.py tests/rules/test_scheduler_vector_indexing_result_frame_0144_rule.py
```
