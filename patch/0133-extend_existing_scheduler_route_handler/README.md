# 0133 — Extend existing Scheduler route handler

0133 follows the 0132 anti-duplication audit: it extends `src/runtime/scheduler_route_handler_minimal.py` instead of creating a new fake worker, new route handler, or new runtime module.

It adds:

- readback helpers for frames written through the existing RouteProxyRuntime;
- an explicit integration decision object documenting reused surfaces;
- tests proving the existing handler is extended and no parallel runtime is created;
- code_rule supplement for anti-duplication.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_scheduler_route_handler_minimal.py tests/rules/test_scheduler_route_handler_existing_integration_0133_rule.py
PYTHONPATH=src:. pytest -q tests/runtime tests/rules
PYTHONPATH=src:. pytest -q
```
