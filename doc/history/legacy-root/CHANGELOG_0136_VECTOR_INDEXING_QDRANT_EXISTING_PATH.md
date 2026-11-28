# Changelog 0136 — vector indexing through existing Qdrant path

Added tests and documentation proving that `VectorProjectionJob` should reuse the existing Qdrant projection membrane and vector collection registry before any production bridge is added.

No production runtime, Scheduler, RouteProxy, Qdrant client, OpenVINO adapter, or durable SQL store was changed.
