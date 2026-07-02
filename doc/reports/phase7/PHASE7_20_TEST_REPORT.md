# Phase 7.20 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_source_candidate_phase7_handoff_contract.py
PYTHONPATH=src:. pytest -q tests/tools/test_source_candidate_phase7_handoff_contract_cli.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
phase 7 handoff contract tests: pass
rules: pass
full suite: pass
```
