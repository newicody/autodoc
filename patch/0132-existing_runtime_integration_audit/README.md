# 0132 — Existing runtime integration audit

This patch adds an audit gate before adding more runtime/handler/adapter modules.

Purpose:

- inventory existing Scheduler/Dispatcher/Policy/RouteProxy/handler/OpenVINO/Qdrant/SQL/EventBus/code_rule surfaces;
- force the decision: reuse existing, extend existing, modify existing, or create new with documented gap;
- prevent parallel runtime wheels.

It adds no live runtime backend and does not modify Scheduler.run().

Apply:

```bash
python apply_patch_queue.py --patch 0132-existing_runtime_integration_audit --dry-run
python apply_patch_queue.py --patch 0132-existing_runtime_integration_audit --commit --push
```

Validate:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_existing_runtime_integration_audit.py tests/rules/test_existing_runtime_integration_audit_0132_rule.py
PYTHONPATH=src:. pytest -q tests/runtime tests/rules
```
