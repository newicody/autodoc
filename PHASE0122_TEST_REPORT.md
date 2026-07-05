# Phase 0122 test report

Validation target for 0122:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/runtime/test_context_graph_export.py
PYTHONPATH=src:. pytest -q tests/rules/test_context_graph_export_0122_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

Local targeted validation during patch generation:

```text
runtime context graph export tests: passed
rule context graph export tests: passed
```
