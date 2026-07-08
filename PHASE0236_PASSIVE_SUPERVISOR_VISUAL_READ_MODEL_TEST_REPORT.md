# Phase 0236 test report — passive supervisor visual read-model

## Intent

Prepare a read-only visual JSON read-model for future VisPy rendering.

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_passive_supervisor_visual_read_model_0236.py
python -m pytest -q tests/tools/test_run_passive_supervisor_visual_read_model_0236.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Boundary

No runtime authority is added. VisPy is not introduced.
