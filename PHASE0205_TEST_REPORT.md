# Phase 0205 Test Report — ControlProxy stale priority zone smoke plan

Status: prepared.

Scope:
- Reads `controlproxy_contract_audit.json`.
- Produces `controlproxy_stale_priority_zone_smoke_plan.json`.
- Reuses 0204 audited ControlProxy and RouteProxy contract surfaces.
- Applies `doc/code-rules/code_rule.md`.
- Updates docs, graph, changelog, manifest, and rule.
- Plans P0206 controlled stale priority zone smoke.
- No Scheduler.run execution.
- No Scheduler.run modification.
- No runtime import.
- No handler call.
- No RouteProxyRuntime preparation.
- No mark_route_frame_stale call.
- No read_route_frame call.
- No writer permit request.
- No frame write by 0205.
- No Scheduler/EventBus instantiation.
- No ControlProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_plan_controlproxy_stale_priority_zone_smoke_0205.py \
  tests/rules/test_controlproxy_stale_priority_zone_smoke_plan_0205_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
