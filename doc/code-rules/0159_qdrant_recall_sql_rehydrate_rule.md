# Code rule — 0159 Qdrant recall -> SQL rehydrate

0159 may add one operator smoke tool:

```text
tools/run_qdrant_recall_sql_rehydrate_smoke.py
```

## Required behavior

The tool may consume a Qdrant recall payload, extract `sql_ref` values, reuse `unique_sql_context_refs_from_recall` when compatible, and rehydrate records through `DbApiSqlContextStore.get_record`.

## Forbidden

Do not create `SQLPersistenceWorker`, `SQLOrchestrator`, `LocalArtifactOrchestrator`, `LocalVectorIndexingOrchestrator`, `SchedulerOpenVINORunner`, `VectorOpenVINOEmbeddingAdapter`, `VectorQdrantProjectionAdapter`, or `QdrantRecallOrchestrator`.

Do not modify Scheduler, RouteProxy, OpenVINO, Qdrant adapter or SQL authority runtime code for this phase.

## Boundary

Qdrant recall is pointer discovery. SQL rehydrate is authority retrieval. SQL remains durable authority. Qdrant remains projection/recall metadata.
