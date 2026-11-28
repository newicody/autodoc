# 0136 — Vector indexing jobs through the existing Qdrant projection path

0136 connects VectorProjectionJob to the existing Qdrant projection adapter by tests and integration documentation.

The goal is to prove that the vector-indexing plan created in 0128 can already target the existing Qdrant projection membrane without inventing another adapter.

## Decision

Do not create a parallel VectorQdrantProjectionAdapter.

Reuse these existing surfaces:

```text
src/inference/qdrant_projection_adapter.py is the existing Qdrant projection membrane
context.vector_collection_registry.VectorCollectionRegistry remains the collection registry
context.vector_indexing_job_plan.VectorProjectionJob remains the projection job contract
```

## Contract alignment

VectorEmbeddingJob produces an embedding result later.

VectorProjectionJob remains the handoff contract for projection.

VectorCollectionRegistry remains the collection registry.

src/inference/qdrant_projection_adapter.py is the existing Qdrant projection membrane.

Scheduler remains the orchestrator and does not import Qdrant.

RouteProxy remains outside Qdrant projection.

SQLContextStore remains durable context authority.

Qdrant stores projections and recall indexes, not durable truth.

## Flow

```text
Scheduler
-> VectorIndexingJobPlan
-> VectorEmbeddingJob
-> existing OpenVINO/E5 embedding membrane
-> VectorProjectionJob
-> existing Qdrant projection membrane
-> collection registry
-> sql_ref preserved for hydration
```

## Non-goals

```text
no new VectorQdrantProjectionAdapter
no Scheduler Qdrant import
no RouteProxy Qdrant import
no Qdrant durable authority
no new worker daemon
```

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: locks Qdrant projection reuse before any production bridge or handler change.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
