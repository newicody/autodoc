# Phase 0284-r3 report — specialist/laboratory message contract

## Result

The missing first-class message envelope now bridges the portable specialist
contract with the existing laboratory visit and `/dev/shm` specialist route
frames. The bridge is immutable and effect-free.

```text
message_contract_added: true
conversation_contract_added: true
portable_specialist_contract_reused: true
existing_laboratory_visit_contract_reused: true
existing_route_frames_reused: true
transport_created: false
runtime_attached: false
```

## Contract surface

```text
SpecialistLaboratoryMessage
SpecialistLaboratoryConversation
build_specialist_demand_message
build_specialist_opinion_message
validate_specialist_laboratory_conversation
```

`SpecialistDemandFrame` and `SpecialistOpinionFrame` remain the local fast
`/dev/shm` data-plane frames. The new message envelope references those frames;
it does not replace them, write them, or move payload commands onto EventBus.

## Next patch

```text
0284-r4-specialist-laboratory-transfer-contract
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0284-r1 identified the missing message contract and 0284-r2 supplied the portable identity; r3 adds only immutable projections over the existing route and visit vocabulary
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: missipy.specialist.laboratory_message.v1
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
message_contract_added: true
conversation_contract_added: true
portable_specialist_contract_reused: true
existing_laboratory_visit_contract_reused: true
existing_route_frames_reused: true
transport_created: false
runtime_attached: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
```
