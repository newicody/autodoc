# Phase 0203 Test Report — Controlled Scheduler hook smoke acceptance

Status: prepared.

Scope:
- Reads `scheduler_hook_dry_run_plan.json`.
- Requires explicit `policy_decision_id`.
- Requires `context.bus.jsonl`.
- Reuses `tools/run_isolated_route_pipeline_smoke.py`.
- Produces `controlled_scheduler_hook_smoke_pipeline.json`.
- Produces `controlled_scheduler_hook_smoke_acceptance.json`.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Closes Bloc C.
- Opens Bloc D after acceptance.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No new Scheduler hook implementation.
- No new runtime handler.
- No new adapter.
- No new bus.
- No ControlProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_run_controlled_scheduler_hook_smoke_acceptance_0203.py \
  tests/rules/test_controlled_scheduler_hook_smoke_acceptance_0203_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
