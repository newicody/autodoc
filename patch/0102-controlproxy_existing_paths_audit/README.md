# 0102 — ControlProxy existing paths audit

This patch audits and marks the existing Scheduler/ControlProxy surrounding paths before any runtime refactor.

It is documentation and rules only. It does not add runtime code.

## Scope

- Classify the current Scheduler-facing ControlProxy helpers as compatibility-wrapper candidates.
- Classify mmap, notifier, lease, generation, lifecycle, lock, materializer, placement, and dispatch-filter code as route-runtime primitives.
- Audit neighboring components that can become duplicates: Scheduler, PolicyEngine, PriorityQueue, Dispatcher, Specialist branch, EventBus, ContextGate, Qdrant, Recorder, and future bridges.
- Add a DOT overlay showing implemented paths, planned convergence, and forbidden duplicate paths.
- Lock 0103 entry criteria: introduce `RouteRuntimeManager` as a narrow runtime facade, not a scheduler-like coordinator.

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
- No ControlProxyRouteCoordinator scheduler-like.
- No RouteRuntimeManager implementation yet.
- No Qdrant, LLM, OpenVINO, NetworkBridge, or HardwareBridge path.

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_controlproxy_existing_paths_audit_0102_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
