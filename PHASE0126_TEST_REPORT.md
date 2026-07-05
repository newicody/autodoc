# Phase 0126 test report

Local validation target:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_vector_contract_indexing_plan.py
PYTHONPATH=src:. pytest -q tests/rules/test_vector_contract_indexing_plan_0126_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Expected targeted result: 11 passed.
