# Phase 0255 test report - Scheduler-owned runtime reuse audit

## Expected validation

```text
python -m compileall -q tools tests
python -m pytest -q tests/tools/test_audit_scheduler_owned_runtime_reuse_0255.py
python -m pytest -q tests/rules/test_scheduler_owned_runtime_reuse_audit_0255_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/audit_scheduler_owned_runtime_reuse_0255.py --format summary
```

## Boundary

The audit is read-only.  It does not import target modules, instantiate
components, call Scheduler.run, connect to PostgreSQL, run OpenVINO, call
Qdrant, call GitHub, or publish events.
