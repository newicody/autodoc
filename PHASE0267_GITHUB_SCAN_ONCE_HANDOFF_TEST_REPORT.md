# Phase 0267 test report - GitHub scan-once handoff

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_github_scan_once_handoff_0267.py
python -m pytest -q tests/tools/test_build_github_scan_once_handoff_0267.py
python -m pytest -q tests/rules/test_github_scan_once_handoff_0267_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Smoke

```text
PYTHONPATH=src:. python tools/build_github_scan_once_handoff_0267.py --closed-frame-report .var/reports/scheduler_managed_closed_result_frame_0264.json --passive-report .var/reports/passive_supervisor_closed_result_frame_observation_0266.json --repository newicody/autodoc --output .var/reports/github_scan_once_handoff_0267.json --format summary
```

## Boundary

GitHub is a review/workflow surface. No remote mutation is performed in 0267.
