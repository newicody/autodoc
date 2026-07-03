# Part 10.5 Cell Lens Local Launch Profiles Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:.:tools pytest -q tests/tools/test_cell_lens_local_launch_profiles.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_lens_local_launch_profiles_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
