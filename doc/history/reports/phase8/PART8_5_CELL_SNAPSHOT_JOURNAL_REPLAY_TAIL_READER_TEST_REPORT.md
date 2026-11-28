# Part 8.5 Cell Snapshot Journal Replay/Tail Reader Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_snapshot_journal_reader.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_snapshot_journal_reader_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
journal reader tests: pass
rules: pass
full suite: pass
```
