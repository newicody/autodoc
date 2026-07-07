# Phase 0171 Test Report — Runtime bus/scheduler artifact audit

Status: prepared.

Scope:
- Audit-only guard for GitHub artifact/dataset integration.
- No new runtime bus.
- No direct VisPy writer.
- No Scheduler loop modification.
- Reuse existing `event.bus` / `context.bus` observation surfaces.
- Reuse existing scheduler route adapter and handler surfaces.

Targeted tests:
```bash
python -m compileall -q src tests tools
python -m pytest -q tests/rules/test_runtime_bus_scheduler_artifact_audit_0171_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

Expected result:
- rules pass
- full suite remains green
