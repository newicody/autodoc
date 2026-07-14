# Phase 0284-r5 report — specialists/laboratories existing-chain smoke

## Result

One `PortableSpecialistDescriptor` is now executed through the already-existing
laboratory closed-loop path:

```text
PortableSpecialistDescriptor
→ existing FakeLaboratoryClosedLoopSmokeCommand
→ Scheduler.emit()
→ PolicyEngine.decide()
→ PriorityQueue
→ Scheduler.run()
→ Dispatcher
→ LaboratoryVisitRequestHandler
→ DeterministicFakeLaboratoryProvider
→ SQL handoff / vector projection / recall / SQL rehydrate
→ demand + opinion SpecialistLaboratoryConversation
→ observable immutable result
```

The smoke calls the existing 0274 closed-loop composition once. It does not
instantiate, own or modify a Scheduler. The selected receipt and opinion are
projected into the 0284-r2/r3 contracts after the existing chain has returned.

```text
fake_specialist_functional: true
portable_specialist_identity_preserved: true
existing_scheduler_path_verified: true
specialist_laboratory_message_contract_closed: true
existing_durable_closed_loop_preserved: true
```

## Transfer boundary

The 0284-r4 visit/transfer contract remains available, but no inter-laboratory
transfer is executed in r5 because the validated runtime currently owns only the
single deterministic local fake laboratory.

```text
transfer_contract_available: true
transfer_execution_performed: false
second_laboratory_required_for_transfer_smoke: true
```

## Next patch

```text
0284-r6-portable-specialist-real-memory-closure
```

The next patch should replace the demonstration projection/recall executors in
this specialist-specific smoke with the controlled real SQL/OpenVINO E5/Qdrant
bindings already completed by phase 0283. It must reuse the current r5 command
and result rather than create another specialist path.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r5 composes existing immutable commands, the existing Scheduler path and the deterministic fake provider; it adds no kernel mechanism, backend dependency, CLI or direct effect
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: missipy.specialist.existing_chain_smoke_result.v1
context_contract_changed: true
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
qdrant_write_performed: inherited_from_injected_existing_smoke
qdrant_search_performed: inherited_from_injected_existing_smoke
sql_write_performed: inherited_from_injected_existing_smoke
llm_or_openvino_added: false
architecture_preserved: true
new_runtime_module_added: true
new_cli_added: false
new_bus_added: false
new_scheduler_added: false
new_laboratory_manager_added: false
new_provider_added: false
new_registry_added: false
existing_scheduler_smoke_reused: true
portable_specialist_contract_reused: true
specialist_laboratory_message_contract_reused: true
specialist_transfer_contract_reused: false
fake_specialist_functional: true
real_specialist_backend_used: false
transfer_execution_performed: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_remains_fast_route_plane: true
control_proxy_remains_lateral: true
projects_repository_change_required: false
```
