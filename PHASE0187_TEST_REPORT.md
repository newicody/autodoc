# Phase 0187 Test Report — Isolated Scheduler route handler smoke

Status: prepared.

Scope:
- Reads `isolated_handler_execution_plan.jsonl`.
- Rebuilds `SchedulerRouteHandlerCommand`.
- Calls existing `handle_scheduler_route_command`.
- Uses `RouteProxyRuntimePolicy` rooted in `isolated_runtime_root`.
- Verifies written frame paths remain under the isolated root.
- Writes optional `isolated_scheduler_route_handler_smoke.jsonl`.
- No Scheduler modification.
- No Scheduler/EventBus instantiation.
- No ControlProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_run_isolated_scheduler_route_handler_smoke_0187.py \
  tests/rules/test_isolated_scheduler_route_handler_smoke_0187_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
