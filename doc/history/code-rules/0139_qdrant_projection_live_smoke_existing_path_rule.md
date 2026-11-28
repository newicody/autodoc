# Code rule addendum — 0139 Qdrant projection live smoke existing path

Before running a Qdrant projection live smoke, audit and reuse the existing projection path.

Mandatory reuse:

```text
reuse src/inference/qdrant_projection_adapter.py
reuse src/context/vector_collection_registry.py
reuse src/context/vector_indexing_job_plan.py
```

Do not create a parallel VectorQdrantProjectionAdapter.

The operator smoke may inspect adapter symbols and delegate to an existing adapter entrypoint.  It must not become a Qdrant adapter itself.

do not import Qdrant from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts.

dry-run must remain the default.
