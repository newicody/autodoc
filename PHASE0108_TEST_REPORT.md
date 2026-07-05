# Phase 0108 test report — ControlProxy route runtime live path

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0108 follows code_rule.md and adds a bounded walking skeleton without changing kernel responsibilities.
live_path_status: green
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

## Intended validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_route_runtime_live_path.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_route_runtime_live_path_0108_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Boundary assertions

- walking skeleton.
- Handler -> RouteRuntimeManager.
- ControlFS + mmap/eventfd data plane.
- EventBus = observation only.
- Route mmap/eventfd = data plane, not EventBus.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
- No Scheduler.run() modification.
- Dispatcher = EventType -> Handler only.
- PolicyEngine = minimal admission before queue.
- PriorityQueue = deterministic execution order.
- Specialist branch owns business logic.

## Local generation validation

```text
git apply --check: OK
py_compile added rule/runtime tests: OK
rule test targeted: OK in generated worktree
runtime test: expected to run in the full repository after 0103/0104 are applied
```
