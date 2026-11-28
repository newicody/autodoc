# Code rule addendum — 0145 local artifact vector indexing runner

Before adding any artifact runner, audit existing Scheduler, RouteProxy, OpenVINO, Qdrant, and SQL surfaces.

For local vector indexing smoke, reuse tools/run_scheduler_vector_indexing_smoke.py for local vector indexing smoke instead of creating a new orchestration path.

Artifact runners may write local operator envelopes under .var/smoke. They may create artifact_input.md, artifact_vector_indexing_report.md, and artifact_vector_indexing_report.json for smoke/operator use.

Artifact runners must not become orchestrators.

Forbidden new wheels:

```text
LocalArtifactOrchestrator
LocalVectorIndexingOrchestrator
SchedulerOpenVINORunner
VectorOpenVINOEmbeddingAdapter
VectorQdrantProjectionAdapter
```

do not create LocalArtifactOrchestrator
do not create LocalVectorIndexingOrchestrator
do not import OpenVINO or Qdrant clients from Scheduler or RouteProxy

OpenVINO remains behind existing inference tools/adapters. Qdrant remains behind existing projection tools/adapters. SQLContextStore remains durable authority.

artifact runners may write local operator envelopes under .var/smoke
artifact runners must not become orchestrators
