# Phase 0284-r6 report — portable specialist real-memory closure

## Result

The portable fake specialist can now reuse the complete real memory path under
explicit execution gates:

```text
Scheduler / fake laboratory
→ SQL authority
→ real OpenVINO multilingual-E5-small passage embedding
→ real Qdrant projection
→ real OpenVINO multilingual-E5-small query embedding
→ real Qdrant reference-only recall
→ SQL rehydration
```

Patch application and automated tests perform no SQL, OpenVINO or Qdrant
effect. A green live result is possible only when the operator executes the
composition with both authorizations and real 0283 bindings.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: r6 composes existing 0261, 0262, 0263, 0283 and 0284-r5 surfaces
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: missipy.specialist.real_memory_closure.v1
context_contract_changed: true
search_commands_bounded: true
external_dependencies_added: false
scheduler_modified: false
network_added: false
network_used_by_patch_application: false
github_api_added: false
qdrant_added: false
qdrant_write_performed_by_tests: false
qdrant_search_performed_by_tests: false
sql_write_performed_by_tests: false
llm_or_openvino_added: false
openvino_executed_by_tests: false
architecture_preserved: true
preview_first: true
existing_0261_embedding_usage_reused: true
existing_0283_scoped_executor_factory_reused: true
existing_0284_r5_specialist_smoke_reused: true
real_sql_authority_used_on_explicit_execute: true
real_openvino_e5_used_on_explicit_execute: true
real_qdrant_projection_used_on_explicit_execute: true
real_qdrant_recall_used_on_explicit_execute: true
qdrant_returns_references_only: true
concrete_dbapi_sql_store_required_on_execute: true
shared_policy_decision_required: true
shared_vector_space_required: true
persistent_effects_reported_on_partial_failure: true
sql_rehydration_verified: true
automatic_cleanup_performed: false
collection_created: false
collection_updated: false
collection_deleted: false
new_qdrant_executor_added: false
new_transport_added: false
new_scheduler_added: false
new_laboratory_manager_added: false
projects_repository_change_required: false
```

## Next step

```text
0284-r7-projects-copilot-specialist-integrated-smoke
```

The next patch should compose the already-existing Projects/Copilot artifact
path with this portable specialist closure. It must not add a second GitHub
workflow engine or move project management into Autodoc.
