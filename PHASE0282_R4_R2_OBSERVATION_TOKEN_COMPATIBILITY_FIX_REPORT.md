# Phase 0282-r4-r2 report — observation token compatibility fix

## Cause

The r4 graph preserved the 0174 `Observation / visualization` anchor but changed
the exact r4 token `Observation only` to lowercase. The r4 rule intentionally
checks that both historical and current anchors coexist.

## Correction

The observation cluster label now contains both exact tokens:

```text
Observation / visualization
Observation only
```

No node, edge, direction, authority boundary or runtime surface changes.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_github_project_v2_append_only_cycle_history_0282_rule.py \
  tests/rules/test_rebuilt_runtime_global_graph_draft_0174_rule.py \
  tests/rules/test_0282_r4_documentation_compatibility_fix_rule.py \
  tests/rules/test_0282_r4_r2_observation_token_compatibility_fix_rule.py

dot -Tsvg \
  doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot \
  -o /tmp/autodoc-0282-r4-r2.svg
```

## Boundaries

```text
runtime_source_modified: false
architecture_topology_modified: false
graph_label_compatibility_only: true
new_runtime_module_added: false
new_cli_added: false
new_adapter_added: false
github_mutation_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
