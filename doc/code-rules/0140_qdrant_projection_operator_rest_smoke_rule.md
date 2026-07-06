# Code rule addendum — 0140 Qdrant projection operator REST smoke

0140 extends the existing Qdrant smoke operator, not the Scheduler.

the existing src/inference/qdrant_projection_adapter.py contract remains the Qdrant projection membrane.

operator REST execution is allowed only in tools/run_qdrant_projection_live_smoke.py.

do not create VectorQdrantProjectionAdapter.

Qdrant stores projection and recall indexes, not durable truth.

SQLContextStore remains durable context authority.

Do not import Qdrant from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts.
