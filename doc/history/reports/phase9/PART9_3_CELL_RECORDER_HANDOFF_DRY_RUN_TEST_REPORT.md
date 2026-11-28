# Part 9.3 Cell Recorder Handoff Dry-Run Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_recorder_handoff.py
PYTHONPATH=src:. pytest -q tests/tools/test_cell_recorder_handoff_dry_run.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_recorder_handoff_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
