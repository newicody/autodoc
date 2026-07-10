# Phase 0265 test report - Closed ResultFrame EventBus observation

## Expected validation

```text
python -m compileall -q src tests tools
python -m pytest -q tests/context/test_closed_result_frame_eventbus_observation_0265.py
python -m pytest -q tests/tools/test_build_closed_result_frame_eventbus_observation_0265.py
python -m pytest -q tests/rules/test_closed_result_frame_eventbus_observation_0265_rule.py
python -m pytest -q tests/rules
python -m pytest -q
```

## Smoke

```text
PYTHONPATH=src:. python tools/build_closed_result_frame_eventbus_observation_0265.py --frame-report .var/reports/scheduler_managed_closed_result_frame_0264.json --output .var/reports/closed_result_frame_eventbus_observation_0265.json --publish-demo --format summary
```

## Boundary

EventBus observation only. Events are facts, not commands. The smoke uses an
in-memory EventBus and does not touch Scheduler.run.
