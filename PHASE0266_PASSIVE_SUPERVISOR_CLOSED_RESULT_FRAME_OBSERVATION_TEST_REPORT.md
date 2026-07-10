# Phase 0266 test report - PassiveSupervisor closed ResultFrame observation

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_passive_supervisor_closed_result_frame_observation_0266.py
python -m pytest -q tests/tools/test_build_passive_supervisor_closed_result_frame_observation_0266.py
python -m pytest -q tests/rules/test_passive_supervisor_closed_result_frame_observation_0266_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Smoke

```text
PYTHONPATH=src:. python tools/build_passive_supervisor_closed_result_frame_observation_0266.py --observation-report .var/reports/closed_result_frame_eventbus_observation_0265.json --output .var/reports/passive_supervisor_closed_result_frame_observation_0266.json --format summary
```

## Boundary

PassiveSupervisor observes only. It does not publish events, execute runtime
steps, or modify Scheduler.run.
