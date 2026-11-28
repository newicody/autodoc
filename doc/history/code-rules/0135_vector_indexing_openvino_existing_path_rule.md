# Code rule addendum — 0135 vector indexing through existing OpenVINO path

Before adding a vector-indexing OpenVINO bridge, audit the existing inference and vector-indexing surfaces.

Required reuse targets:

```text
reuse context.vector_indexing_job_plan.VectorEmbeddingJob
reuse inference.openvino_embedding_adapter.OpenVINOEmbeddingText
reuse inference.openvino_embedding_adapter.build_embedding_vector
```

Do not create a parallel VectorOpenVINOEmbeddingAdapter.

Do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts.

The only acceptable next production change is to extend an existing inference module or handler with a documented gap and tests proving that no suitable existing function already covers the need.
