# 0159 — Qdrant recall -> SQL rehydrate

## Decision

0159 adds one operator smoke tool:

```text
tools/run_qdrant_recall_sql_rehydrate_smoke.py
```

It consumes a Qdrant recall payload or a Qdrant-style previous P1 result, extracts `sql_ref`, and rehydrates durable records with:

```text
DbApiSqlContextStore.get_record(sql_ref)
```

## Flow

```text
Qdrant recall payload
-> sql_ref extraction
-> DbApiSqlContextStore.get_record(sql_ref)
-> qdrant_recall_sql_rehydrate_result.json
-> qdrant_recall_sql_rehydrate_report.md
```

## Reused surfaces

| Surface | Role |
| --- | --- |
| `src/inference/qdrant_projection_adapter.py` | existing projection/recall helper vocabulary, including `unique_sql_context_refs_from_recall` |
| `src/context/sql_context_store.py` | existing durable SQL authority, including `DbApiSqlContextStore.get_record` |
| `src/context/sql_context_hydrator.py` | existing rehydration vocabulary |

## Boundary

0159 does not create `SQLPersistenceWorker`, `SQLOrchestrator`, `LocalArtifactOrchestrator`, `LocalVectorIndexingOrchestrator`, `SchedulerOpenVINORunner`, `VectorOpenVINOEmbeddingAdapter`, `VectorQdrantProjectionAdapter`, or `QdrantRecallOrchestrator`.

SQL remains durable authority. Qdrant remains projection/recall metadata.
