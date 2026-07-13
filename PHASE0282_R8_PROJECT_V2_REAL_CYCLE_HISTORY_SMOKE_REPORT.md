# Phase 0282-r8 report — ProjectV2 real cycle-history smoke

## Result

The implementation sequence 0282-r1 through r8 is complete. A real ProjectV2
cycle can now be represented locally, planned deterministically, previewed
through the existing GitHub adapter and executed only after an exact digest
confirmation.

```text
0282_series_status: implementation_complete
```

A real user-run preview and, separately, an explicitly authorized test mutation
remain operational validation steps rather than patch-application side effects.

## Next series

```text
0283-qdrant-controlled-real-executor
```

The next series must reuse the existing SQL-reference/Qdrant projection
contracts and must not introduce one Qdrant authority per specialist.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r8 composes existing r4-r7 contracts and reuses the sole mutation adapter
live_path_status: controlled
live_path_uses_real_backend: true
context_contract_version: missipy.github.project_v2_real_cycle_history_smoke.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
existing_r7_adapter_reused: true
preview_is_default: true
exact_smoke_digest_required_for_execution: true
new_scheduler_added: false
new_mutation_transport_added: false
view_grouping_automated: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
```

`live_path_uses_real_backend` is true because the CLI delegates an explicitly
authorized execution to the already-existing r7 `gh api` adapter. The default
path remains a local preview with no network call.
