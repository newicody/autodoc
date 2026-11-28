# Phase 7.18 Test Report

## Commands

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/context/test_source_candidate_external_probe_local_replay.py
PYTHONPATH=src:. pytest -q tests/tools/test_source_candidate_external_probe_local_replay_cli.py
PYTHONPATH=src:. pytest -q tests/rules
PYTHONPATH=src:. pytest -q
```

## Expected

```text
external probe local replay tests: pass
rules: pass
full suite: pass
```
