# Code rule addendum — 0141-r1 Qdrant smoke idempotency

Qdrant operator smoke tools must treat HTTP 409 during collection ensure as an idempotent collection-already-exists result.

This exception applies only to `tools/run_qdrant_projection_live_smoke.py` collection ensure.  It must not be generalized into Scheduler, RouteProxy, PolicyEngine, Dispatcher, or context contracts.

Do not create VectorQdrantProjectionAdapter for this case; extend the existing operator smoke tool and keep `src/inference/qdrant_projection_adapter.py` as the projection membrane.
