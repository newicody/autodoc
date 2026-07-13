# Changelog 0283-r7 — Qdrant real binding preview-first CLI

- Added one CLI around the existing r2/r4/r5/r6 surfaces.
- Made local readiness the default behavior.
- Added an independent explicit live collection metadata gate.
- Added separate projection and recall authorization flags.
- Required live operational readiness before any requested effect.
- Kept projection and recall previews client-free.
- Opened the SQLite authority read-only only for recall execute.
- Added atomic JSON report output and a concise summary format.
- Added no collection administration, Scheduler path or transport.

```text
architecture_preserved: true
preview_first: true
live_readiness_is_explicit: true
operation_authorization_is_explicit: true
projection_authorization_separate: true
recall_authorization_separate: true
existing_r2_configuration_reused: true
existing_r4_projection_binding_reused: true
existing_r5_recall_binding_reused: true
existing_r6_readiness_reused: true
collection_created: false
collection_updated: false
collection_deleted: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
