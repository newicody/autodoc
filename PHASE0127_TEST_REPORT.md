# PHASE 0127 TEST REPORT

Target: vector collection registry contract.

Validated locally:

```text
PYTHONPATH=src:. python -m compileall -q src tests
PYTHONPATH=src:. pytest -q tests/runtime/test_vector_collection_registry.py
PYTHONPATH=src:. pytest -q tests/rules/test_vector_collection_registry_0127_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q tests/runtime tests/rules
```

Result:

```text
targeted tests: 10 passed
tests/rules: 62 passed
tests/runtime + tests/rules: 147 passed
```
