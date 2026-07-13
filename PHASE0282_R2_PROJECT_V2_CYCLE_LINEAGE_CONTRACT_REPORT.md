# Phase 0282-r2 report — ProjectV2 cycle-lineage contract

## Result

The local lineage contract is deterministic, immutable, serializable and
strictly free of IO. It is ready to receive normalized query-only ProjectV2
parent/theme data in the next phase.

## Next phase

```text
0282-r3-projectv2-parent-theme-query-normalization
```

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_cycle_lineage_0282.py \
  tests/rules/test_github_project_v2_cycle_lineage_0282_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r1 documented the missing contract and existing immutable-contract rules are sufficient
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: missipy.github.project_v2_cycle_lineage.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
reuse_audit_completed: true
existing_suitable_module_found: false
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
graphql_query_added: false
graphql_mutation_added: false
github_mutation_performed: false
projects_repository_change_required: false
```

`live_path_status` is `n/a` because this phase adds a pure versioned contract,
not an executable capability or adapter.
