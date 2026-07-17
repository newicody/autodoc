# 0260-r10-db_api_sql_context_store_schema_bootstrap_adapter

Fixes the next real execution failure:

```text
sqlite3.OperationalError: no such table: sql_context_records
```

The adapter now calls an existing schema bootstrap hook when the bound
DbApiSqlContextStore exposes one, without inventing a schema or starting
PostgreSQL.

Apply:

```bash
python apply_patch_queue.py --patch 0260-r10-db_api_sql_context_store_schema_bootstrap_adapter --commit --push --allow-dirty
```
