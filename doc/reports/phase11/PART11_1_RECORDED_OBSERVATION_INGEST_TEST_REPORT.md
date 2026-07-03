# Part 11.1 Recorded Observation Ingest Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_recorded_observation_ingest.py
PYTHONPATH=src:. pytest -q tests/tools/test_ingest_recorded_observations_to_cell_journal.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_recorded_observation_ingest_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
