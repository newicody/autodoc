# Code rule addendum — 0143 Scheduler vector indexing smoke

Scheduler vector indexing smoke must reuse the existing scheduler route handler.

Rules:

- RouteProxy frame IO must reuse src/runtime/route_proxy_runtime_minimal.py.
- Strict vector execution must reuse tools/run_local_vector_indexing_live_smoke.py.
- OpenVINO must remain behind the existing E5/OpenVINO membrane and operator tool.
- Qdrant must remain behind the existing Qdrant projection membrane and operator tool.
- do not create SchedulerOpenVINORunner.
- do not create LocalVectorIndexingOrchestrator.
- do not create VectorOpenVINOEmbeddingAdapter.
- do not create VectorQdrantProjectionAdapter.
- do not modify Scheduler.run().
