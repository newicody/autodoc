# Code rule addendum — 0144 scheduler vector indexing result frame

Vector indexing result frames must reuse the existing scheduler route handler.

Rules:

- Result frame IO must reuse src/runtime/route_proxy_runtime_minimal.py.
- Result frame command handling must reuse src/runtime/scheduler_route_handler_minimal.py.
- Strict vector execution must remain behind tools/run_local_vector_indexing_live_smoke.py.
- do not create a VectorIndexingResultWorker.
- do not create LocalVectorIndexingOrchestrator.
- do not import OpenVINO or Qdrant client into Scheduler or RouteProxy.
- do not modify Scheduler.run().

The result frame is an operator/smoke artifact until a later durable job/result contract is explicitly wired.
