# Part 10.2 Local Read-Only SSE Endpoint Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_cell_snapshot_sse_server.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_snapshot_sse_server_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
