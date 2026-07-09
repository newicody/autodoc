# Phase 0257 test report - Scheduler-owned runtime registry

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_owned_runtime_registry_0257.py
python -m pytest -q tests/tools/test_build_scheduler_owned_runtime_registry_0257.py
python -m pytest -q tests/rules/test_scheduler_owned_runtime_registry_0257_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/build_scheduler_owned_runtime_registry_0257.py --source-map .var/reports/scheduler_owned_runtime_reuse_source_map_0256.json --output .var/reports/scheduler_owned_runtime_registry_0257.json --format summary
```

## Boundary

Registry only.  No runtime manager, no component instantiation, no
Scheduler.run modification, no PostgreSQL/OpenVINO/Qdrant/GitHub execution, and
no EventBus publish.
