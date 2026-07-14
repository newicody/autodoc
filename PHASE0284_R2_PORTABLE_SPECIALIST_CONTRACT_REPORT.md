# Phase 0284-r2 report — portable specialist contract

## Result

The first-class portable specialist contract now exists. A specialist keeps one
stable `specialist_ref`, declares its capabilities and accepted/produced
contracts, records bounded execution preferences and lists compatible
laboratories without binding a provider or attaching a runtime component.

```text
portable_specialist_contract_added: true
stable_specialist_identity: true
existing_laboratory_contract_reused: true
existing_specialist_route_frames_reused: true
provider_attached: false
runtime_attached: false
```

## Contract surface

```text
SpecialistCapabilityContract
SpecialistExecutionProfile
SpecialistLaboratoryBinding
PortableSpecialistDescriptor
validate_portable_specialist_visit_contract
```

The compatibility validator accepts the shared fields already used by the
existing route and laboratory visit contracts. It does not import either
runtime module and performs no dispatch or visit.

## Next patch

```text
0284-r3-specialist-laboratory-message-contract
```

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 0284-r1 explicitly proved the first-class portable specialist contract was the only missing contract at this boundary; r2 adds immutable stdlib-only contracts and pure validation without attaching runtime authority
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: missipy.specialist.descriptor.v1
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
existing_laboratory_contract_reused: true
existing_specialist_route_frames_reused: true
portable_specialist_contract_added: true
stable_specialist_identity: true
provider_attached: false
runtime_attached: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
```
