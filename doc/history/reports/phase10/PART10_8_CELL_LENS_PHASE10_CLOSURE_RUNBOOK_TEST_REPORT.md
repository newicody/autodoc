# Part 10.8 Cell Lens Phase 10 Closure Runbook Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/rules/test_cell_lens_phase10_closure_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
closure rule tests: pass
rules: pass
full suite: pass
```
