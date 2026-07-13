# Phase 0282-r3 report — ProjectV2 parent/theme query normalization

## Result

The existing live query-only ProjectV2 path now reads native parent/sub-issue
relations. The new pure normalizer converts the resulting snapshot and existing
Project fields into deterministic r2-compatible references.

## Next phase

```text
0282-r4-projectv2-append-only-cycle-history-projection
```

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_parent_theme_query_normalization_0282.py \
  tests/rules/test_github_project_v2_parent_theme_query_normalization_0282_rule.py \
  tests/context/test_github_project_v2_query_only_snapshot_0272.py

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r1 justified the missing surface and r2 established the immutable references
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: missipy.github.project_v2_parent_theme_normalization.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
github_api_query_extended: true
qdrant_added: false
llm_or_openvino_added: false
existing_query_extended: true
parallel_query_transport_added: false
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
github_api_client_added: false
graphql_mutation_added: false
github_mutation_performed: false
projects_repository_change_required: false
```

No new network client is added. The current live GraphQL client will use the
extended query document, while normalization remains a pure local operation.
