# Changelog 0283-r8 — Qdrant real closed-loop smoke

- Added a preview-first full SQL → E5 → Qdrant → SQL smoke tool.
- Reused existing 0261, r4, r5 and r6 surfaces.
- Added a dedicated SQLite smoke authority by default.
- Locked multilingual-E5-small vectors to dimension 384.
- Required separate smoke and persistent-point authorizations.
- Verified returned SQL reference, rehydrated record and authority body.
- Reported point IDs and SQL fixture cleanup requirements.
- Added no automatic Qdrant or SQL cleanup.
- Added no Scheduler, executor, transport, proxy, bus or SHM/MMIO path.

```text
architecture_preserved: true
preview_first: true
existing_0261_embedding_usage_reused: true
existing_r4_projection_binding_reused: true
existing_r5_recall_binding_reused: true
existing_r6_readiness_reused: true
real_sql_authority_used_on_execute: true
real_openvino_e5_used_on_execute: true
real_qdrant_projection_used_on_execute: true
real_qdrant_recall_used_on_execute: true
qdrant_returns_references_only: true
sql_rehydration_verified: true
automatic_cleanup_performed: false
collection_created: false
collection_updated: false
collection_deleted: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
projects_repository_change_required: false
external_dependencies_added: false
```
