# Phase 0272-r3 test report

## Result

0272-r3 reads the real user ProjectV2 `newicody/2` through GraphQL query
operations only and writes a deterministic immutable local snapshot.  The
Actions artifact path remains secondary.

## Review block

```text
code_rule_review: done
reuse_audit: github_project_push_frame_config reused
new_module_justification: no ProjectV2 GraphQL query client exists
context_contract_version: missipy.github.project_v2_query_only_snapshot.v1
external_dependencies_added: false
network_boundary: stdlib urllib.request in CLI only
graphql_mutation_allowed: false
remote_mutation_allowed: false
direct_issue_rest_scan_added: false
scheduler_modified: false
sql_or_qdrant_write_added: false
shm_changed: false
```

## Validation performed

```text
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. python -m pytest -q tests/context/test_github_project_v2_query_only_snapshot_0272.py
PYTHONPATH=src:. python -m pytest -q tests/tools/test_run_github_project_v2_query_only_snapshot_0272.py
PYTHONPATH=src:. python -m pytest -q tests/rules/test_github_project_v2_query_only_snapshot_0272_rule.py
```

Fixture mode is offline and performs no network call.  Live validation must be
performed locally with a token that has read access to ProjectV2 `newicody/2`.

## Construction result

```text
base_commit: 8971877361bf7d1d1b127700304088791de57b78
compileall_targeted: passed
targeted_tests: 10 passed
graphviz_dot: passed
network_used_by_tests: false
remote_mutation_performed: false
```
