# Phase 0275-r8-r1 test report — ProjectV2 0272 compatibility

## Reported failure

```text
4 failed, 2705 passed, 1 skipped
```

All four failures stopped in the common 0272 configuration loader with:

```text
github artifact scan config rejected: interval_not_10, trigger_source
```

The affected tests were the two deployment-readiness CLI fixtures and the
two ProjectV2 query-only snapshot CLI fixtures.

## Correction

Existing 0272 sections are restored exactly:

```text
artifact_source
scan
safety
deployment_readiness
```

The new section remains:

```text
workflow_dispatch
```

## Validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_github_project_v2_0272_config_compatibility_0275_r8_r1_rule.py \
  tests/tools/test_run_github_project_system_deployment_readiness_0272.py \
  tests/tools/test_run_github_project_v2_query_only_snapshot_0272.py \
  tests/context/test_github_project_v2_en_cours_dispatch_0275_r8.py \
  tests/tools/test_github_project_v2_en_cours_dispatch_tools_0275_r8.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Phase review

```text
config_0272_contract_restored: true
workflow_dispatch_section_preserved: true
scheduler_modified: false
scheduler_run_modified: false
project_mutation_added: false
issue_mutation_added: false
non_stdlib_dependencies_added: false
```
