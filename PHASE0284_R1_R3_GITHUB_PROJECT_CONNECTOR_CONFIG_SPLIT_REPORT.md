# Phase 0284-r1-r3 — GitHub project connector configuration split

## Result

The ProjectV2 query-only configuration and the outbound Projects workflow
dispatch configuration are now separate. Dispatch operations must receive the
dedicated safe example explicitly with `--config`; the already-divergent legacy
CLI is not modified by this boundary patch. Stale `newicody/autodoc-ideas`
example references are replaced by `newicody/projects`.

The Projects bundle now includes a cumulative installation guide that records
the copy workflow, GitHub Actions settings, local connector setup and current
limitations.

## Boundaries

```text
scheduler_modified: false
new_project_mode_added_to_autodoc: false
active_projects_workflow_added_to_autodoc_root: false
query_only_config_contains_workflow_dispatch: false
dispatch_example_safe_by_default: true
dispatch_cli_default_modified: false
projects_installation_readme_added: true
sql_write_allowed: false
qdrant_write_allowed: false
```

## Code rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: configuration and documentation boundary correction only
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_library_added: false
```
