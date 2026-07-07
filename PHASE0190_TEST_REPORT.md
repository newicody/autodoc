# Phase 0190 Test Report — Policy-scoped isolated route pipeline smoke

Status: prepared.

Scope:
- Keeps 0189 as the isolated pipeline smoke.
- Preserves append-only `scheduler.route_requests.jsonl`.
- Adds `scheduler.route_requests.policy_scoped.jsonl` for the current
  `policy_decision_id`.
- Ensures downstream 0184 through 0188 stages process only policy-scoped route
  requests.
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
