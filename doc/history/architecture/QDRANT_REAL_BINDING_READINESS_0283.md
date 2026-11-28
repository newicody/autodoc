# Qdrant real binding readiness — 0283-r6

## Purpose

Inspect whether a validated 0283 binding can safely proceed to controlled
projection or recall, without changing the working architecture.

```text
architecture_preserved: true
existing_r2_configuration_reused: true
existing_r3_factory_inspection_reused: true
existing_dependency_inspection_reused: true
```

## Two readiness levels

### Local readiness

```text
validated r2 configuration
→ existing dependency inspection
→ existing r3 factory inspection
→ optional environment secret presence
→ no client construction
→ no network
```

Local readiness proves that the process can construct the existing scoped
executor. It does not claim that the Qdrant service or target collection is
available.

### Operational readiness

Operational readiness is available only when `live_probe=true`:

```text
local readiness green
→ construct one short-lived qdrant-client
→ read get_collection(target)
→ verify allowed status
→ verify vector dimension
→ verify distance metric
→ close client
```

The accepted default statuses are `green` and `yellow`. A red, unavailable or
incompatible collection is not operationally ready.

## Collection contract

The current target is an unnamed dense-vector collection:

```text
collection = autodoc_context_embeddings
dimension = 384
distance = Cosine
```

Named-vector schemas are rejected until the Autodoc target contract explicitly
carries a vector name.

## Effect-specific readiness

```text
projection_ready
= operational_ready
  and projection requested
  and allow_write

recall_ready
= operational_ready
  and recall requested
  and allow_search
```

Readiness does not execute either effect.

## Explicit non-goals

```text
live_probe_is_explicit: true
live_probe_read_only: true
collection_created: false
collection_updated: false
collection_deleted: false
qdrant_write_performed: false
qdrant_search_performed: false
sql_read_performed: false
sql_write_performed: false
qdrant_started: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
