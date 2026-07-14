# Phase 0284-r1-r3-r4 — GitHub project connector trigger contract fix

## Result

The split configuration now preserves the existing read-only artifact-ingestion
contract while keeping the outbound `workflow_dispatch` connector in its own
safe configuration. The query-only and push-frame examples use
`github_action_on_ticket_event`; the dedicated Projects dispatch example remains
separate and disabled by default.

## Boundaries

```text
scheduler_modified: false
runtime_tool_modified: false
legacy_artifact_loader_modified: false
project_v2_query_only_contains_workflow_dispatch: false
artifact_ingestion_trigger: github_action_on_ticket_event
outbound_workflow_dispatch_separate: true
dispatch_example_safe_by_default: true
sql_write_allowed: false
qdrant_write_allowed: false
```

## Code rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: configuration contract repair after full-suite validation
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_library_added: false
```
