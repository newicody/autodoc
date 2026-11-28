# Part 12.1 Baby Fork Smoke Project Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_baby_fork_smoke_project.py
PYTHONPATH=src:. pytest -q tests/tools/test_run_baby_fork_smoke_project.py
PYTHONPATH=src:. pytest -q tests/rules/test_baby_fork_smoke_project_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
