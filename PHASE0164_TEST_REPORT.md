# Phase 0164 test report — GitHub read-only artifact fetch smoke

## Target tests

```text
PYTHONPATH=src:. pytest -q tests/tools/test_github_read_only_artifact_fetch_smoke_0164.py tests/rules/test_github_read_only_artifact_fetch_0164_rule.py
```

## Target smoke

```text
python tools/run_github_read_only_artifact_fetch_smoke.py . --execute --format json
```

## Expected result

```text
status: ok
read_only: true
probe_allowed: true
external_call_performed: false
github_payload_dry_run: true
github_payload_remote_mutation: false
mutation_allowed: false
```

## Boundary

0164 does not write SQL/Qdrant, does not call GitHub, does not use external
network, does not execute Scheduler, LLM or OpenVINO, and does not ingest the
Autodoc/MissiPy development repository as a business artifact corpus.
