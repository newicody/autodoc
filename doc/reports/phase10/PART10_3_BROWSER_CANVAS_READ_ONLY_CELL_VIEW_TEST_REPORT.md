# Part 10.3 Browser Canvas Read-Only Cell View Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_cell_snapshot_browser_view_server.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_snapshot_browser_view_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
