# Phase 0237 test report — passive supervisor visual layout model

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_passive_supervisor_visual_layout_model_0237.py
python -m pytest -q tests/tools/test_run_passive_supervisor_visual_layout_model_0237.py
python -m pytest -q tests/rules/test_passive_supervisor_visual_layout_model_0237_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Boundary

This patch is read-only and renderer-free. It does not modify Scheduler,
EventBus, PassiveSupervisorSink, proxy, SHM, policy, SQL, Qdrant, or GitHub
runtime behavior.
