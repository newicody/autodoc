# Phase 0256 test report - Scheduler-owned runtime reuse source map

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_scheduler_owned_runtime_reuse_source_map_0256.py
python -m pytest -q tests/tools/test_build_scheduler_owned_runtime_reuse_source_map_0256.py
python -m pytest -q tests/rules/test_scheduler_owned_runtime_reuse_source_map_0256_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/build_scheduler_owned_runtime_reuse_source_map_0256.py --output .var/reports/scheduler_owned_runtime_reuse_source_map_0256.json --format summary
```

## Boundary

Read-only.  No target module imports, no component instantiation, no
Scheduler.run call, no PostgreSQL connection, no OpenVINO inference, no Qdrant
call, no GitHub call, no EventBus publish.
