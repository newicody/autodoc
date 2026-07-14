# Phase 0284-r1-r1 report — EventBus VisPy live bridge

## Result

The existing EventBus can now feed the existing VisPy Cell Lens journal continuously when the application is started with an explicit `MISSIPY_CELL_LENS_JOURNAL` path. The desktop VisPy launch profile tails the same journal every 0.25 seconds.

```text
existing_eventbus_reused: true
existing_cell_observation_contract_reused: true
existing_cell_snapshot_contract_reused: true
existing_append_only_journal_reused: true
existing_vispy_tail_reader_reused: true
optional_activation_only: true
observer_failure_isolated: true
```

## Live path

```text
real EventBus
→ generic passive subscription
→ CellObservationEvent
→ real append-only missipy.cell.v1 journal
→ existing VisPy --tail reader
→ observable live view
```

The bridge is composed in the application entry point, not in the Scheduler. It does not emit commands or events and does not own any system state.

## Copilot ProjectV2 finding

The current Projects workflow produces a Copilot advisory artifact but does not publish its status or summary into ProjectV2 and does not update the source Issue. Therefore the advisory cannot appear in a board/table view yet. That remote mutation is deliberately excluded from this patch and must remain behind the existing controlled-publication boundary.

## Next patches

```text
support follow-up: 0284-r1-r2-copilot-projectv2-visibility-projection
functional chain: 0284-r2-portable-specialist-contract
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: the patch reuses the established EventBus observation, Cell Lens contract, append-only journal and VisPy tail adapter; no new programming technique or authority is introduced
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: missipy.cell.v1
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
qdrant_write_performed: false
qdrant_search_performed: false
sql_write_performed: false
llm_or_openvino_added: false
architecture_preserved: true
new_runtime_module_added: true
new_cli_added: false
new_bus_added: false
new_scheduler_added: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
projects_repository_change_required_for_this_patch: false
```
