# Qdrant scoped executor factory composition — 0283-r3

## Purpose

Construct the already-existing concrete Qdrant executor from a valid 0283-r2
configuration, then immediately wrap it with the already-existing SQL-authority
scope.

```text
architecture_preserved: true
existing_client_factory_reused: true
existing_concrete_executor_reused: true
existing_sql_scope_wrapper_reused: true
```

No transport, Scheduler path, ControlProxy path, EventBus path, SHM path or MMIO
path is introduced.

## Construction sequence

```text
valid 0283-r2 binding configuration
→ inspect existing qdrant-client dependency readiness
→ resolve optional API key at the construction boundary
→ build_qdrant_client_projection_executor
→ SqlAuthorityScopedQdrantExecutor
→ return scoped runtime binding
```

The existing effect gate remains attached to the concrete executor. The factory
never explicitly calls `upsert_points` or `search_vector`.

The current working architecture remains:

```text
Scheduler
→ existing 0262/0263 use cases
→ injected QdrantProjectionExecutor protocol
→ SqlAuthorityScopedQdrantExecutor
→ QdrantClientProjectionExecutor
→ existing qdrant-client transport
```

Future local SHM/memfd and MMIO/DMA work remains an orientation only. The
ControlProxy remains lateral control infrastructure and is not inserted here.

## Boundaries

```text
new_qdrant_executor_added: false
new_transport_added: false
scheduler_modified: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
data_operation_performed: false
qdrant_write_performed: false
qdrant_search_performed: false
sql_write_performed: false
projects_repository_change_required: false
external_dependencies_added: false
```
