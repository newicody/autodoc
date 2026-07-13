# Phase 0282-r4 report — ProjectV2 append-only cycle history

## Result

The r2 lineage and r3 query-only normalization are now projected into an
immutable local cycle history. The projection distinguishes append, identical
replay, collision and rejection without performing any IO.

The architecture documentation now exposes three synchronized views:

```text
global current architecture
current 0282 development axis
beginning-versus-current comparison
```

The operational 0174 DOT graph is refreshed. The large `00_global.dot` remains
unchanged as heritage and roadmap memory.

## Next phase

```text
0282-r5-projectv2-parent-sub-ticket-mutation-plan
```

## Validation

```bash
PYTHONPATH=src:. python -m pytest -q \
  tests/context/test_github_project_v2_append_only_cycle_history_0282.py \
  tests/rules/test_github_project_v2_append_only_cycle_history_0282_rule.py

dot -Tsvg \
  doc/docs/architecture/runtime/174_rebuilt_runtime_global_current_state.dot \
  -o /tmp/autodoc-0282-global.svg

PYTHONPATH=src:. python -m pytest -q tests/rules
PYTHONPATH=src:. python -m pytest -q
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r1 justified the missing history projection and r2/r3 provide reusable immutable inputs
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: missipy.github.project_v2_cycle_history_projection.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
new_runtime_module_added: true
new_cli_added: false
new_adapter_added: false
filesystem_write_added: false
graphql_mutation_added: false
github_mutation_performed: false
projects_repository_change_required: false
heritage_global_graph_modified: false
operational_global_graph_refreshed: true
```

`live_path_status` is `transition`: the projection consumes contracts derived
from the real query-only ProjectV2 path, but persistence and mutation planning
are deliberately deferred.
