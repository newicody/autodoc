# Phase 0275-r8 test report — En cours dispatch, Copilot and groups

## Validated predecessor

```text
2698 passed, 1 skipped
patch queue green
manual controlled workflow and artifacts confirmed
```

## Generation checks

- all added Python sources compile;
- focused unit tests pass in a synthetic source tree;
- generated patch passes `git apply --check` against complete expected files;
- no binary, `.pyc`, `.pyo`, cache or font artifact is included.

## Repository validation

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools

PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_en_cours_dispatch_0275_r8.py \
  tests/tools/test_github_project_v2_en_cours_dispatch_tools_0275_r8.py \
  tests/rules/test_github_project_v2_en_cours_dispatch_copilot_groups_0275_r8_rule.py \
  tests/rules/test_github_projects_research_theme_event_templates_0275_r7_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Code-rule review

```text
reuse_audit: 0272 query-only snapshot and change detection reused
new_project_reader_added: false
new_scheduler_added: false
scheduler_modified: false
scheduler_run_modified: false
daemon_added: false
openrc_service_added: false
project_mutation_added: false
issue_mutation_added: false
scoped_workflow_dispatch_added: true
token_serialized: false
sql_write_added: false
qdrant_write_added: false
non_stdlib_dependencies_added: false
```
