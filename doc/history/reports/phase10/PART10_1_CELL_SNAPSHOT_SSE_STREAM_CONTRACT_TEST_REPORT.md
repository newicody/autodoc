# Part 10.1 Cell Snapshot SSE Stream Contract Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_cell_snapshot_sse.py
PYTHONPATH=src:. pytest -q tests/tools/test_cell_snapshot_sse_dry_run.py
PYTHONPATH=src:. pytest -q tests/rules/test_cell_snapshot_sse_stream_contract_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```
