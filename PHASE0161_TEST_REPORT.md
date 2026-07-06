# Phase 0161 test report — Qdrant live recall SQL rehydrate

## Manual precondition

The query embedding smoke produced:

```text
dimension: 384
normalized: True
l2_norm: 1.0
vector_len: 384
text: query: P1 closed loop artifact vector indexing SQL persistence
```

## Target tests

```bash
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q \
  tests/tools/test_qdrant_live_recall_sql_rehydrate_0161.py \
  tests/rules/test_qdrant_live_recall_sql_rehydrate_0161_rule.py
```

## Target operator execution

```bash
python tools/run_qdrant_live_recall_sql_rehydrate_smoke.py . \
  --query-vector-json .var/smoke/artifacts/0161/0161_query_embedding.json \
  --db-path .var/local/sql_context_store.sqlite3 \
  --execute \
  --format json
```

## Expected result

```text
status: ok
query_vector_dimension: 384
recall_hit_count >= 1
rehydrate_status: ok
hydrated_count >= 1
missing_count: 0
```

## Boundary

0161 is an operator smoke only. It does not create a SQL worker, query
orchestrator, Scheduler runner, OpenVINO adapter or Qdrant adapter.
