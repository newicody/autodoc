# 0104-controlproxy_route_runtime_handler

Adds a thin ControlProxy route runtime handler binding.

The patch wires the existing `ControlProxySchedulerRouteRequestHandler` injection point to `RouteRuntimeManager` without modifying Scheduler, Dispatcher, PriorityQueue or PolicyEngine.

## Scope

- Add `src/runtime/controlproxy_route_runtime_handler.py`.
- Add runtime tests for Scheduler handler injection to RouteRuntimeManager.
- Add rule tests and architecture docs.
- Add a root-attached runtime `.dot` overlay.

## Non-goals

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or PolicyEngine modification.
- No EventBus creation and no bus duplication.
- No global priority management in ControlProxy.
- No policy/zone authority inside ControlProxy.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_route_runtime_handler.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_route_runtime_handler_0104_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
