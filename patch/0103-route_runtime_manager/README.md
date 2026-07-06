# 0103 — RouteRuntimeManager

This patch introduces `RouteRuntimeManager` as the single importable runtime facade for ControlProxy / ControlFS route primitives.

It deliberately does not add a CLI, service, daemon, watcher, Scheduler change, Dispatcher change, policy change, priority engine, EventBus ownership, or specialist business logic.

## Scope

- Add `src/runtime/route_runtime_manager.py`.
- Add runtime tests for materialization, lifecycle, cleanup, denied/reuse no-effect decisions and table loading.
- Add rule tests that lock the 0101 simplification boundaries.
- Add docs and a root-attached runtime `.dot` overlay.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_route_runtime_manager.py
PYTHONPATH=src:. pytest -q tests/rules/test_route_runtime_manager_0103_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Notes

`RouteRuntimeManager` is not a scheduler-like coordinator. It receives an already-decided `RoutePrepareDecision` and composes existing route runtime primitives only.
