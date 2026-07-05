# Phase 0117 test report

Patch: `0117-sql_context_hydrator`

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_sql_context_hydrator.py
PYTHONPATH=src:. pytest -q tests/rules/test_sql_context_hydrator_0117_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Local focused validation on reconstructed 0116 base:

```text
compileall: OK
runtime 0117: OK
rules 0117: OK
```
