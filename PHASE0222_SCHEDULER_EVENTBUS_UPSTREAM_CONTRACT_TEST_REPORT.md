# Phase 0222 Test Report — Scheduler EventBus upstream contract

## Scope

Written contract only. No runtime code added.

## Local validation

```text
git apply --check patch/0222-scheduler_eventbus_upstream_contract/patch.diff : OK
python -m compileall -q tests : OK
python -m pytest -q tests/rules/test_scheduler_eventbus_upstream_contract_0222_rule.py : OK
```

## Authority boundary

```text
Scheduler remains upstream orchestration authority.
EventBus remains canonical observation transport.
PassiveSupervisorSink remains downstream-only.
No Scheduler.run() call or modification.
No proxy, SHM, policy, SQL, Qdrant, GitHub, or VisPy mutation.
```
