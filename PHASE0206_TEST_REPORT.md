# Phase 0206 Test Report — ControlProxy RouteProxy coherence acceptance

Status: prepared.

Scope:
- Reads `controlproxy_stale_priority_zone_smoke_plan.json`.
- Requires explicit `policy_decision_id`.
- Requires `context.bus.jsonl`.
- Reuses `tools/run_isolated_route_pipeline_smoke.py`.
- Produces `isolated_route_pipeline_smoke.json`.
- Produces `controlproxy_routeproxy_coherence_acceptance.json`.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Closes Bloc D.
- Opens Bloc E after acceptance.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No new ControlProxy runtime.
- No new RouteProxy runtime.
- No new Scheduler hook implementation.
- No direct mark_route_frame_stale call.
- No ControlProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_run_controlproxy_routeproxy_coherence_acceptance_0206.py \
  tests/rules/test_controlproxy_routeproxy_coherence_acceptance_0206_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
