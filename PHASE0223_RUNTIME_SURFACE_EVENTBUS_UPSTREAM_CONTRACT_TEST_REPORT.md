# Phase 0223 Test Report — Runtime surface EventBus upstream contract

## Scope

Written contract only. No runtime code added.

## Local validation

```text
git apply --check patch/0223-r1-runtime_surface_eventbus_upstream_contract/patch.diff : OK
python -m compileall -q tests : OK
python -m pytest -q tests/rules/test_runtime_surface_eventbus_upstream_contract_0223_rule.py : OK
```

## Authority boundary

```text
RouteProxy, ControlProxy, SHM, and Policy remain upstream runtime/control surfaces.
EventBus remains canonical observation transport.
PassiveSupervisorSink remains downstream-only.
No proxy control, SHM write, raw mmap read, policy decision, Scheduler.run(), SQL/Qdrant/GitHub mutation, or VisPy runtime path.
```
