# Phase 7.10 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_dot_remove_code_rule_references.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Cleanup command

```bash
python tools/dot_remove_code_rule_references.py \
  --root . \
  --apply \
  --check \
  --report-file doc/maintenance/dot_code_rule_cleanup_report.json
```

## Expected

```text
DOT cleanup tool tests: pass
rules: pass
full suite: pass after cleanup
```
