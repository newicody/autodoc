# Changelog 0152 — SQLContextStore configured DB path

Changed:

- `tools/run_sql_context_store_controlled_write_smoke.py` now resolves the SQL DB path from `--db-path`, `AUTODOC_SQL_CONTEXT_DB`, or `.var/local/sql_context_store.sqlite3`.

Added:

- configured DB path tests and code-rule tests
- architecture/code-rule docs

0152 keeps the existing `DbApiSqlContextStore.upsert_record` write path and only stabilizes where the DB-API SQLite database lives by default.
