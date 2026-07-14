# Phase 0284-r4 report — specialist/laboratory transfer contract

## Result

The portable specialist can now be represented across a temporary laboratory
visit or a durable laboratory transfer while preserving its stable identity,
conversation, parent visit, context and return route.

```text
SpecialistTransferRequest
→ SpecialistTransferVisitPlan
→ existing LaboratoryVisitRequest fields
→ existing Scheduler.emit()
→ SpecialistTransferResult
```

A temporary `visit` returns the active specialist location to the origin after
completion. A durable `transfer` leaves the active location at the target.
Neither case directly invokes a provider or creates a transport.

## Next patch

```text
0284-r5-specialists-laboratories-existing-chain-smoke
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0284-r1 explicitly identified the missing transfer contract; r4 adds immutable plans and continuity validation over r2/r3 and the existing laboratory visit vocabulary
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: missipy.specialist.transfer_request.v1
context_contract_changed: true
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
new_laboratory_manager_added: false
new_provider_added: false
new_registry_added: false
portable_specialist_contract_reused: true
specialist_laboratory_message_contract_reused: true
existing_laboratory_visit_contract_reused: true
specialist_transfer_contract_added: true
specialist_identity_preserved: true
visit_lineage_preserved: true
transport_created: false
runtime_attached: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
```
