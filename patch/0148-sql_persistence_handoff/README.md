# 0148 — SQL persistence handoff

This patch adds a handoff-only SQL persistence envelope for validated artifact vector-indexing results.

It reuses existing artifact output files and does not write SQL rows yet.

Validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_sql_persistence_handoff_0148.py tests/rules/test_sql_persistence_handoff_0148_rule.py
```
