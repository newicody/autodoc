# Phase 0282-r4-r1 report — documentation compatibility fix

## Cause

The 0282-r4 architecture refresh replaced historical strings that are still
locked by the 0270 and 0174 compatibility rules. Runtime behavior and the new
0282 topology were correct; only stable documentation anchors were lost.

## Correction

- restore `Current operational baseline — 0270` as an explicitly historical
  compatibility heading;
- restore `canonical index refreshed by 0270` as an explicitly historical
  compatibility phrase;
- retain all nine required 0174 graph labels while preserving the 0282-r4
  nodes, edges and current-state label;
- do not revert any 0282-r4 code, schema or architecture content.

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/rules/test_operational_documentation_consolidation_0270_rule.py \
  tests/rules/test_rebuilt_runtime_global_graph_draft_0174_rule.py \
  tests/rules/test_0282_r4_documentation_compatibility_fix_rule.py

PYTHONPATH=src:. python -m pytest -q tests/rules
```

## Boundaries

```text
runtime_source_modified: false
architecture_topology_reverted: false
new_runtime_module_added: false
new_cli_added: false
new_adapter_added: false
github_mutation_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
