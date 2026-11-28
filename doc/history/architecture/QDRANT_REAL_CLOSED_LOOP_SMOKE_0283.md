# Qdrant real closed-loop smoke — 0283-r8

## Purpose

Prove the complete current local path without adding another runtime:

```text
dedicated SQL fixture
→ existing 0261 OpenVINO multilingual-E5-small passage embedding
→ existing r4 controlled Qdrant projection
→ existing 0261 query embedding
→ existing r5 controlled Qdrant recall
→ reference-only SQL refs
→ existing SQLContextStore rehydration
→ authority body verification
```

```text
architecture_preserved: true
preview_first: true
existing_0261_embedding_usage_reused: true
existing_r4_projection_binding_reused: true
existing_r5_recall_binding_reused: true
existing_r6_readiness_reused: true
```

## Preview

Preview is the default. It uses an in-memory fixture mapping and the existing
deterministic 384-dimensional demo embedding only to validate composition.

```text
SQL database opened: false
OpenVINO executed: false
Qdrant client constructed: false
Qdrant write: false
Qdrant search: false
```

## Execute

Execute requires all of:

```text
--execute
--authorize-smoke
--authorize-persistent-smoke-point
--policy-decision-id policy:...
```

The model directory must exist. The E5 dimension is locked to 384.

Execution creates or updates one record in the dedicated default database:

```text
.var/smoke/qdrant_real_closed_loop_0283.sqlite3
```

It does not write into the normal SQL authority unless the operator explicitly
overrides `--db-path`.

## Verification

The smoke is valid only when:

```text
projection write acknowledged
Qdrant recall executed
fixture sql_ref returned
fixture record rehydrated
rehydrated body equals SQL authority body
```

```text
real_sql_authority_used_on_execute: true
real_openvino_e5_used_on_execute: true
real_qdrant_projection_used_on_execute: true
real_qdrant_recall_used_on_execute: true
qdrant_returns_references_only: true
sql_rehydration_verified: true
```

## Cleanup

The tool does not delete Qdrant points or SQL records. The report contains the
dedicated database path, SQL ref, collection and projected point IDs.

```text
automatic_cleanup_performed: false
```

This prevents an automated smoke from deleting a pre-existing point or context
record by mistake.

## Architecture unchanged

```text
collection_created: false
collection_updated: false
collection_deleted: false
scheduler_modified: false
new_scheduler_added: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
