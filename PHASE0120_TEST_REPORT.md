# Phase 0120 test report

Patch: `0120-llm_specialist_adapter`

Expected validation:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_llm_specialist_adapter.py
PYTHONPATH=src:. pytest -q tests/rules/test_llm_specialist_adapter_0120_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Local focused validation on reconstructed 0119 base:

```text
compileall: OK
runtime 0120: OK
rules 0120: OK
```
