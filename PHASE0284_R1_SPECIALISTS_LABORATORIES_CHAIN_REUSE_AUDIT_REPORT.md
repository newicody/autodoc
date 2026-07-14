# Phase 0284-r1 report — specialists/laboratories chain reuse audit

## Result

The existing laboratory chain is already substantial and must remain the
foundation of phase 0284. The missing surface is not a laboratory framework; it
is a first-class portable specialist contract that bridges the existing
specialist route frames and laboratory visit contracts.

## Reuse decision

```text
existing_laboratory_contract_reused: true
existing_fake_provider_reused: true
existing_scheduler_visit_binding_reused: true
existing_specialist_route_frames_reused: true
existing_handoff_recall_smoke_reused: true
existing_qdrant_chain_reused: true
portable_specialist_contract_missing: true
```

## Next patch

```text
0284-r2-portable-specialist-contract
```

The contract should cover a specialist descriptor, capabilities, accepted and
produced contracts, execution preferences and allowed laboratory bindings. It
must preserve `specialist_ref` portability and must not bind the specialist to
the deterministic fake provider.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r1 audits and selects existing wheels before authorizing the single missing portable specialist contract
live_path_status: existing_chain_reuse_confirmed
live_path_uses_real_backend: false
context_contract_version: missipy.specialists_laboratories.chain_reuse_audit.v1
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
new_laboratory_manager_justified: false
new_scheduler_justified: false
eventbus_observation_only: true
sql_remains_authority: true
qdrant_projection_recall_only: true
dev_shm_fast_route_plane: true
control_proxy_lateral_only: true
projects_repository_change_required: false
```

The new runtime module is an effect-free source audit only. It imports none of
the audited runtime modules.
