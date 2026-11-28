# 0161 — Qdrant live recall -> SQL rehydrate

## Decision

0161 adds one operator smoke for the live Qdrant recall boundary:

```text
tools/run_qdrant_live_recall_sql_rehydrate_smoke.py
```

It consumes a query embedding JSON produced by the existing E5/OpenVINO CLI,
calls Qdrant REST `/points/search`, writes a Qdrant-style recall payload, then
delegates durable record retrieval to the existing 0159 SQL rehydrate tool.

## Audit result

The 0161 audit found existing recall surfaces:

| Surface | Role |
| --- | --- |
| `tools/embed_e5.py` | existing query embedding CLI |
| `tools/run_qdrant_projection_live_smoke.py` | existing live Qdrant REST smoke surface using `/points/search` |
| `tools/run_qdrant_recall_sql_rehydrate_smoke.py` | existing 0159 recall payload -> SQL rehydrate operator |
| `src/inference/qdrant_projection_adapter.py` | existing `QdrantRecallQuery`, `QdrantRecallResult`, `QdrantProjectionExecutor.search_vector`, `QdrantProjectionAdapter.recall_by_vector` |
| `src/context/sql_context_store.py` | existing durable SQL authority |

The manual query embedding proof produced:

```text
text: query: P1 closed loop artifact vector indexing SQL persistence
dimension: 384
normalized: true
l2_norm: 1.0
vector_len: 384
```

## Flow

```text
query embedding JSON
-> Qdrant REST /collections/{collection}/points/search
-> Qdrant recall payload with sql_ref
-> 0159 SQL rehydrate
-> hydrated context
```

## Boundary

0161 does not create:

- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`
- `QdrantRecallOrchestrator`
- `QueryRecallOrchestrator`

0161 does not modify runtime Python under `src/`.

## Operator command

```bash
python tools/run_qdrant_live_recall_sql_rehydrate_smoke.py . \
  --query-vector-json .var/smoke/artifacts/0161/0161_query_embedding.json \
  --db-path .var/local/sql_context_store.sqlite3 \
  --execute \
  --format json
```

## Closure definition

0161 is validated when the result reports:

```text
status: ok
query_vector_dimension: 384
recall_hit_count >= 1
rehydrate_status: ok
hydrated_count >= 1
missing_count: 0
sql_refs contains sql:*
```

SQL remains durable authority. Qdrant remains projection/recall metadata.
