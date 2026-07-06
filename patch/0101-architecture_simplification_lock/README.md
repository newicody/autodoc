# 0101 — architecture simplification lock

This patch locks the simplified architecture before more ControlProxy runtime code is added.

It is documentation and rules only. It does not add runtime code.

## Scope

- Lock Scheduler, PolicyEngine, PriorityQueue, Dispatcher, Handler, Specialist, ControlProxy/RouteRuntimeManager, EventBus, and route data-plane responsibilities.
- Reject the scheduler-like ControlProxy coordinator direction.
- Define the next roadmap: RouteRuntimeManager first, then handler slimming, then priority/admission and bus/data-plane cleanup.
- Add a root-attached DOT overlay for the simplified architecture.
- Add a rule test that keeps these decisions executable.

## Guardrails

- No CLI.
- No daemon/service/OpenRC.
- No resident watcher.
- No runtime code.
- No Scheduler.run() modification.
- No PriorityQueue modification.
- No Dispatcher implementation modification.
- No PolicyEngine implementation modification.
- No EventBus implementation modification.
- No new bus.
- No Qdrant, LLM, OpenVINO, NetworkBridge, or HardwareBridge path.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_simplification_lock_0101_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
