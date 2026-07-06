# Code rule — 0160 query recall rehydrate contract

0160 may add one operator smoke tool:

```text
tools/run_query_recall_rehydrate_contract_smoke.py
```

## Required behavior

The tool may:

- normalize user query text to the E5 `query:` role;
- accept an optional query embedding artifact produced by an existing E5/OpenVINO surface;
- accept a Qdrant recall payload carrying `sql_ref` pointers;
- delegate SQL rehydration to the existing 0159 tool;
- write local JSON/Markdown reports under `.var/smoke/artifacts/0160`.

## Required reuse

The tool must document and reuse existing surfaces:

- `tools/embed_e5.py`
- `tools/run_qdrant_recall_sql_rehydrate_smoke.py`
- `tools/run_qdrant_projection_live_smoke.py`
- `tools/search_e5_corpus.py`
- `src/inference/e5_pipeline.py`
- `src/inference/qdrant_projection_adapter.py`
- `src/context/sql_context_store.py`
- `DbApiSqlContextStore.get_record`
- `unique_sql_context_refs_from_recall`

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

0160 is a contract/operator smoke only. It is not a new query runtime.

SQL remains durable authority. Qdrant remains projection/recall metadata.
