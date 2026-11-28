# Code rule addendum — 0136 vector indexing through existing Qdrant path

Before adding a vector-indexing Qdrant bridge, audit the existing inference, vector-indexing, and registry surfaces.

Required reuse targets:

```text
reuse or extend src/inference/qdrant_projection_adapter.py
reuse context.vector_collection_registry.VectorCollectionRegistry
reuse context.vector_indexing_job_plan.VectorProjectionJob
```

Do not create a parallel VectorQdrantProjectionAdapter.

Do not import Qdrant from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts.

Qdrant stores projections and recall indexes, not durable truth. SQLContextStore remains durable context authority.

The next production change must extend an existing inference/vector module or handler with a documented gap and tests proving that no suitable existing function already covers the need.
