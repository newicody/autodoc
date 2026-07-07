# Phase 0199 Test Report — Controlled dev RouteProxy smoke execution

Status: prepared.

Scope:
- Reads `controlled_dev_routeproxy_smoke_plan.json`.
- Requires explicit `policy_decision_id`.
- Requires `context.bus.jsonl`.
- Reuses `tools/run_isolated_route_pipeline_smoke.py`.
- Produces `isolated_route_pipeline_smoke.json` under `target_runtime_root`.
- Produces `controlled_dev_routeproxy_smoke_execution.json`.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Explicitly unlocks controlled dev execution.
- Requires P0200 post-execution audit and acceptance.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_run_controlled_dev_routeproxy_smoke_0199.py \
  tests/rules/test_controlled_dev_routeproxy_smoke_execution_0199_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
