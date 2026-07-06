# 0143 — Scheduler vector indexing smoke

Adds one operator smoke tool that reuses the existing Scheduler route handler and RouteProxy runtime to write a vector indexing request frame, then hands execution to the existing strict local vector indexing smoke tool.

No new Scheduler runner, vector orchestrator, OpenVINO adapter, Qdrant adapter, daemon, or RouteProxy worker is introduced.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_scheduler_vector_indexing_smoke_0143.py tests/rules/test_scheduler_vector_indexing_smoke_0143_rule.py
```
