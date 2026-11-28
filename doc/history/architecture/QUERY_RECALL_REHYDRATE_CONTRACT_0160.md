# 0160 — Query recall rehydrate contract

## Decision

0160 locks the boundary for a user query entering the recall side of P1:

```text
query text
-> E5 query-role text
-> existing query embedding surface
-> Qdrant recall payload carrying sql_ref
-> 0159 SQL rehydrate
-> hydrated context
```

This phase does not introduce a new adapter, worker, runner, orchestrator or
backend client. It adds only one operator smoke:

```text
tools/run_query_recall_rehydrate_contract_smoke.py
```

## Audit result

The 0160 audit found existing surfaces:

| Surface | Role |
| --- | --- |
| `tools/embed_e5.py` | existing E5/OpenVINO query embedding CLI |
| `tools/run_qdrant_projection_live_smoke.py` | existing Qdrant live projection smoke |
| `tools/run_qdrant_recall_sql_rehydrate_smoke.py` | existing 0159 recall payload -> SQL rehydrate operator |
| `tools/search_e5_corpus.py` | existing local E5 search CLI |
| `src/inference/e5_pipeline.py` | existing E5/OpenVINO pipeline |
| `src/inference/qdrant_projection_adapter.py` | existing projection/recall helper vocabulary, including `unique_sql_context_refs_from_recall` |
| `src/context/sql_context_store.py` | existing durable SQL authority, including `DbApiSqlContextStore.get_record` |

## Contract

0160 requires:

```text
query_text starts with query:
recall payload contains sql_ref
0159 returns hydrated_count >= 1
0159 returns missing_count = 0
```

## Boundary

0160 does not create:

- `SQLPersistenceWorker`
- `SQLOrchestrator`
- `LocalArtifactOrchestrator`
- `LocalVectorIndexingOrchestrator`
- `SchedulerOpenVINORunner`
- `VectorOpenVINOEmbeddingAdapter`
- `VectorQdrantProjectionAdapter`
- `QdrantRecallOrchestrator`
- `QueryRecallOrchestrator`

0160 does not modify runtime Python under `src/`.

## Operator command

Dry-run:

```bash
python tools/run_query_recall_rehydrate_contract_smoke.py . --format markdown
```

Execute against the 0158/0159 validated path:

```bash
python tools/run_query_recall_rehydrate_contract_smoke.py .   --query-text "P1 closed loop artifact vector indexing SQL persistence"   --recall-json .var/smoke/artifacts/0158/p1_closed_loop_operator_result.json   --db-path .var/local/sql_context_store.sqlite3   --execute   --format json
```

## Closure definition

0160 is validated when the result reports:

```text
status: ok
query_text starts with query:
rehydrate_status: ok
hydrated_count >= 1
missing_count: 0
sql_refs contains sql:artifact/vector-indexing/0158
```

SQL remains durable authority. Qdrant remains projection/recall metadata.
