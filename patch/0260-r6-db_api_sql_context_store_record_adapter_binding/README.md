# 0260-r6-db_api_sql_context_store_record_adapter_binding

Adds a minimal wrapper around the existing `DbApiSqlContextStore` object.

The real store may expose `upsert_record(record)` and expect `record.context_ref`.
The 0259 usage path expects a store-like object with `controlled_write(payload)`.
This patch adapts the existing object at the 0260 binding boundary without
modifying 0259 and without creating a SQL store.

Apply on top of the current 0260 state:

```bash
python apply_patch_queue.py --patch 0260-r6-db_api_sql_context_store_record_adapter_binding --commit --push --allow-dirty
```
