# Phase 0163 test report — GitHub external artifact existing builders

## Target tests

```text
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q tests/tools/test_github_external_artifact_smoke_0162.py tests/tools/test_github_external_artifact_existing_builders_0163.py tests/rules/test_github_external_artifact_boundary_0162_rule.py tests/rules/test_github_external_artifact_existing_builders_0163_rule.py
```

## Target smoke

```text
python tools/run_github_external_artifact_smoke.py . --execute --format json | tee .var/smoke/artifacts/0162/github_external_artifact_smoke_execute.json
```

## Expected result

```text
status: ok
external_repository: newicody/autodoc-ideas
source_candidate_ref starts with artifact:github-source:
sql_context_ref starts with sql:
publication_ref starts with github:project-publication:
review_ref starts with github-review:publication:
publish_to_github: false
external_call_performed: false
```

## Boundary

0163 reuses existing builders and does not introduce a GitHub adapter,
orchestrator, SQL write, Qdrant write, GitHub API call, external network,
Scheduler execution, LLM execution, OpenVINO execution or automatic publication.
