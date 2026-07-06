# Phase 0160 test report — query recall rehydrate contract

## Audit

The 0160 audit found existing surfaces for query embedding, Qdrant recall
payload handling, and SQL rehydrate. The patch therefore adds a contract smoke
only and does not add a new adapter/backend/orchestrator.

## Target tests

```bash
env -u AUTODOC_SQL_CONTEXT_DB PYTHONPATH=src:. pytest -q   tests/tools/test_query_recall_rehydrate_contract_0160.py   tests/rules/test_query_recall_rehydrate_contract_0160_rule.py
```

## Target operator execution

```bash
python tools/run_query_recall_rehydrate_contract_smoke.py .   --query-text "P1 closed loop artifact vector indexing SQL persistence"   --recall-json .var/smoke/artifacts/0158/p1_closed_loop_operator_result.json   --db-path .var/local/sql_context_store.sqlite3   --execute   --format json
```

## Expected result

```text
status: ok
query_text starts with query:
rehydrate_status: ok
hydrated_count >= 1
missing_count: 0
sql_refs contains sql:artifact/vector-indexing/0158
```

## Boundary

0160 is an operator smoke only. It does not create a SQL worker, query
orchestrator, Scheduler runner, OpenVINO adapter or Qdrant adapter.
