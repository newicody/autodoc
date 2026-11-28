# Part 8.3 Cell Snapshot Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_snapshot.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_snapshot_contract_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
cell snapshot tests: pass
rules: pass
full suite: pass
```
