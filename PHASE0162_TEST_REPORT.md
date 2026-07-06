# Phase 0162 test report — GitHub external artifact smoke

## Target tests

```text
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q tests/tools/test_github_external_artifact_smoke_0162.py tests/rules/test_github_external_artifact_boundary_0162_rule.py
```

## Target smoke

```text
python tools/run_github_external_artifact_smoke.py . --execute --format json | tee .var/smoke/artifacts/0162/github_external_artifact_smoke_execute.json
```

## Expected result

```text
status: ok
external_repository: newicody/autodoc-ideas
publish_to_github: false
external_call_performed: false
publication_review_required: true
```

## Boundary

0162 does not write SQL/Qdrant, does not call GitHub, does not use external
network, does not execute the Scheduler, LLM or OpenVINO, and does not ingest
the Autodoc development repository as a business artifact corpus.
