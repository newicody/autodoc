# Phase 7.17 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_source_candidate_external_probe_local_audit_trail.py
PYTHONPATH=src:. pytest -q tests/tools/test_source_candidate_external_probe_local_audit_trail_cli.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
external probe local audit trail tests: pass
rules: pass
full suite: pass
```
