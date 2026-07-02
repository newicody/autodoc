# Phase 7.16 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_source_candidate_external_probe_operator_summary.py
PYTHONPATH=src:. pytest -q tests/tools/test_source_candidate_external_probe_operator_summary_cli.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
external probe operator summary tests: pass
rules: pass
full suite: pass
```
