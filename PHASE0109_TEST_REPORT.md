# Phase 0109 test report — ControlProxy compatibility wrapper cleanup

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0109 marks legacy helpers as compatibility wrappers and keeps the simplified kernel/runtime responsibilities locked.
live_path_status: cleanup
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
```

## Intended validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_controlproxy_compatibility_wrappers.py
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_compatibility_wrappers_0109_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Boundary assertions

- 0109 compatibility wrapper cleanup.
- prepare_route_for_scheduler.
- handle_scheduler_route_request.
- compatibility wrappers.
- do not extend legacy wrappers.
- Handler -> RouteRuntimeManager.
- No Scheduler.run() modification.
- Dispatcher = EventType -> Handler only.
- PolicyEngine = minimal admission before queue.
- PriorityQueue = deterministic execution order.
- EventBus = observation only.
- Route mmap/eventfd = data plane, not EventBus.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
- Specialist branch owns business logic.
- No scheduler-like ControlProxy coordinator.
