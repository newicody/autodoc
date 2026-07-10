# Rule 0271-r2 — qdrant-client projection executor

1. Reuse `inference.qdrant_projection_adapter.QdrantProjectionExecutor`.
2. The only new runtime dependency is the official qdrant-client SDK, pinned and justified.
3. Require a typed policy decision and separate write/search gates before SDK effects.
4. Preserve `payload.sql_ref`; SQL remains the durable authority.
5. Never start, stop, install or configure the Qdrant daemon.
6. Never modify Scheduler, the SHM data-plane, RouteProxy or ControlProxy.
7. Convert SDK failures to a typed serializable failure and fail closed on missing SQL refs.
8. Keep tests independent from a real Qdrant service through client/model injection.
