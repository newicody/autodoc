# Phase 0238 test report — passive supervisor visual pipeline smoke

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_passive_supervisor_visual_pipeline_0238.py
python -m pytest -q tests/tools/test_run_passive_supervisor_visual_pipeline_smoke_0238.py
python -m pytest -q tests/rules/test_passive_supervisor_visual_pipeline_smoke_0238_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Direct smoke

```text
PYTHONPATH=src:. python tools/run_passive_supervisor_visual_pipeline_smoke_0238.py --format summary
```

## Boundary

This patch composes existing local tools only. It does not modify Scheduler,
EventBus, PassiveSupervisorSink, proxy, SHM, policy, SQL, Qdrant, or GitHub
runtime behavior.
