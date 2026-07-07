# Phase 0184 Test Report — Route request to command dry-run plan

Status: prepared.

Scope:
- Reads `scheduler.route_requests.jsonl`.
- Builds reviewable kwargs for `build_single_frame_route_command`.
- Writes optional `route_request_to_command_dry_run_plan.jsonl`.
- No handler import.
- No builder call.
- No handler call.
- No Scheduler modification.
- No EventBus instantiation.
- No ControlProxy/RouteProxy frame write.
- No GitHub API/network.
- No conversion/inference/SQL/Qdrant/VisPy writes.

Validation:

```bash
python -m compileall -q src tests tools
python -m pytest -q \
  tests/tools/test_build_route_request_to_command_dry_run_plan_0184.py \
  tests/rules/test_route_request_to_command_dry_run_plan_0184_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```
