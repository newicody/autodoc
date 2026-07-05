# Phase 0125-r2 test report

Validation performed on reconstructed base through 0124.

```bash
PYTHONPATH=src:. python -m compileall -q src tests
PYTHONPATH=src:. pytest -q tests/runtime/test_scheduler_deliberation_route_contract.py
PYTHONPATH=src:. pytest -q tests/rules/test_scheduler_deliberation_route_contract_0125_r2_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Results:

- Targeted runtime/rule tests: 10 passed.
- tests/rules: 54 passed.
- Full pytest: 126 passed.
