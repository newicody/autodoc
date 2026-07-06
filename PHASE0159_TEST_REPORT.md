# Phase 0159 test report — Qdrant recall SQL rehydrate

## Target tests

```bash
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q \
  tests/tools/test_qdrant_recall_sql_rehydrate_0159.py \
  tests/rules/test_qdrant_recall_sql_rehydrate_0159_rule.py
```

## Target operator execution

```bash
python tools/run_qdrant_recall_sql_rehydrate_smoke.py . \
  --recall-json .var/smoke/artifacts/0158/p1_closed_loop_operator_result.json \
  --db-path .var/local/sql_context_store.sqlite3 \
  --execute \
  --format json
```

Expected: `status: ok`, `hydrated_count >= 1`, `missing_count: 0`.
