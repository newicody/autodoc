# Code rule addendum — 0141 local vector indexing live smoke

Before adding any local vector indexing runner, audit existing operator surfaces and reuse them.

Required reuse:

```text
reuse tools/run_openvino_e5_live_smoke.py
reuse tools/run_qdrant_projection_live_smoke.py
reuse src/inference/openvino_embedding_adapter.py
reuse src/inference/qdrant_projection_adapter.py
reuse src/context/vector_indexing_job_plan.py
```

Forbidden wheels:

```text
do not create LocalVectorIndexingOrchestrator
do not create VectorOpenVINOEmbeddingAdapter
do not create VectorQdrantProjectionAdapter
do not import OpenVINO from Scheduler or RouteProxy
do not import Qdrant from Scheduler or RouteProxy
do not parse human-only embedding previews as full vectors
```

machine-readable vector handoff must be explicit.  If the existing E5 operator cannot emit a full vector, extend the existing embedding CLI/membrane instead of creating a parallel embedding implementation.
