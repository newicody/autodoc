# Part 8.6 Synthetic Cell Population Generator Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_snapshot_synthetic.py
PYTHONPATH=src:. pytest -q tests/tools/test_generate_synthetic_cell_journal.py
PYTHONPATH=src:. pytest -q tests/rules/test_synthetic_cell_population_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
synthetic generator tests: pass
tool tests: pass
rules: pass
full suite: pass
```
