# Phase 0284-r1-r3-r2 — GitHub project connector rule migration

## Result

The historical 0275 rule assertions now validate the separated connector
configuration introduced by 0284-r1-r3. The ProjectV2 query-only example keeps
all remote mutation gates closed and no longer contains a workflow-dispatch
section. The dedicated Projects dispatch example targets `newicody/projects`
and remains disabled by default.

## Boundaries

```text
scheduler_modified: false
runtime_tool_modified: false
query_only_config_modified: false
dispatch_config_modified: false
historical_rule_contract_migrated: true
query_only_contains_workflow_dispatch: false
dispatch_example_remote_gates_enabled: false
sql_write_allowed: false
qdrant_write_allowed: false
```

## Code rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: executable rule alignment after an intentional configuration boundary change
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_library_added: false
```
