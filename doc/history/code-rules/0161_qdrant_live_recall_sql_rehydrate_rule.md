# Code rule — 0161 Qdrant live recall SQL rehydrate

0161 may add one operator smoke tool:

```text
tools/run_qdrant_live_recall_sql_rehydrate_smoke.py
```

## Required behavior

The tool may:

- read a query vector JSON produced by `tools/embed_e5.py`;
- call Qdrant REST `/points/search`;
- normalize the Qdrant response into a recall payload carrying `sql_ref`;
- delegate SQL rehydration to the existing 0159 tool;
- write local JSON/Markdown reports under `.var/smoke/artifacts/0161`.

## Required reuse

The tool must document and reuse existing surfaces:

- `tools/embed_e5.py`
- `tools/run_qdrant_projection_live_smoke.py`
- `tools/run_qdrant_recall_sql_rehydrate_smoke.py`
- `src/inference/qdrant_projection_adapter.py`
- `src/context/sql_context_store.py`
- `QdrantProjectionExecutor.search_vector`
- `QdrantProjectionAdapter.recall_by_vector`
- `QdrantRecallQuery`
- `QdrantRecallResult`
- `unique_sql_context_refs_from_recall`
- `DbApiSqlContextStore.get_record`

## Forbidden

Do not create:

- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`
- `QdrantRecallOrchestrator`
- `QueryRecallOrchestrator`

Do not modify Scheduler, RouteProxy, OpenVINO, Qdrant adapter or SQL authority
runtime code for this phase.

## Boundary

0161 is a live operator smoke only. It is not a new query runtime.

SQL remains durable authority. Qdrant remains projection/recall metadata.
