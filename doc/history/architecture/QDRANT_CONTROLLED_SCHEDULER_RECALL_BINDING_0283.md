# Qdrant controlled Scheduler recall binding — 0283-r5

## Purpose

Bind the existing Scheduler-owned 0263 Qdrant recall and SQL rehydration use
case to the existing r3 scoped real-Qdrant executor.

```text
architecture_preserved: true
existing_0263_usage_reused: true
existing_r3_factory_reused: true
existing_sql_store_reused: true
```

## Current path retained

```text
Scheduler-owned command/use case
→ scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263
→ injected SqlAuthorityScopedQdrantExecutor
→ QdrantClientProjectionExecutor.search_vector
→ reference-only Qdrant hits
→ unique SQL context refs
→ existing SQLContextStore.get_record
→ hydrated durable records
```

Qdrant remains an index and recall projection. SQL remains the content
authority.

## Preview

```text
execute=false
→ validate recall-only r2 configuration
→ derive or accept qdrant-query reference
→ run 0263 with execute=false
→ no client construction
→ no Qdrant search
→ no SQL read
```

```text
preview_constructs_client: false
preview_reads_sql: false
```

## Execute

```text
execute=true
→ build existing r3 scoped binding
→ inject binding.executor into 0263
→ search Qdrant once
→ extract unique SQL refs
→ rehydrate through injected existing SQL store
→ close binding
```

## Recall-only effect boundary

```text
requested_operations = ("recall",)
allow_search = true
allow_write = false
```

The requested limit must not exceed the configured
`projection_policy.max_recall_hits`.

## Architecture explicitly unchanged

```text
qdrant_search_requires_execute: true
qdrant_returns_refs_only: true
sql_remains_authority: true
new_scheduler_added: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
