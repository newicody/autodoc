# Part 8.1 Aider Dormant Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_local_ai_dormant_cleanup.py
PYTHONPATH=src:. pytest -q tests/rules/test_local_ai_dormant_cleanup_rule.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
cleanup tests: pass
rules: pass
full suite: pass
```
