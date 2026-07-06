# 0152 — SQLContextStore configured DB path

Apply with `apply_patch_queue.py --patch 0152-sql_context_store_configured_db_path`.

This patch keeps the 0151 `DbApiSqlContextStore.upsert_record` write path and only stabilizes DB path resolution:

1. `--db-path`
2. `AUTODOC_SQL_CONTEXT_DB`
3. `.var/local/sql_context_store.sqlite3`
