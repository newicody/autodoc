# Part 9.2 Cell Observation Event Adapter Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_observation_event.py
PYTHONPATH=src:. pytest -q tests/tools/test_convert_cell_observation_events.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_observation_event_adapter_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
