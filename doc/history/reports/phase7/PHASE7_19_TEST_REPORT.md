# Phase 7.19 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_source_candidate_phase7_closure_report.py
PYTHONPATH=src:. pytest -q tests/tools/test_source_candidate_phase7_closure_report_cli.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
phase 7 closure report tests: pass
rules: pass
full suite: pass
```
