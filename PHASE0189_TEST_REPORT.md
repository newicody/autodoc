# Phase 0189 Test Report — Isolated route pipeline smoke

Status: prepared.

Scope:
- Reads `context.bus.jsonl`.
- Reuses 0179 and 0184 through 0188 stages.
- Writes consolidated `isolated_route_pipeline_smoke.json`.
- Writes RouteProxy frames only under explicit `isolated_runtime_root`.
- No new runtime handler.
- No Scheduler modification.
- No Scheduler/EventBus instantiation.
- No ControlProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_run_isolated_route_pipeline_smoke_0189.py \
  tests/rules/test_isolated_route_pipeline_smoke_0189_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
