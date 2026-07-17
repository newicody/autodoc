# 0260-r5-db_api_sql_context_store_upsert_record_adapter

Fixes the execution side of 0260 after the binding selected the real
`context.sql_context_store.DbApiSqlContextStore`.

The real store exposes `upsert_record(record)` and expects a record-like object
with `context_ref`.  The 0259 wrapper was still passing a raw dict payload.
This patch adapts the wrapper to build a compatible record object while keeping
the existing store contract intact.

Apply on top of the current 0260 state:

```bash
python apply_patch_queue.py --patch 0260-r5-db_api_sql_context_store_upsert_record_adapter --commit --push --allow-dirty
```
