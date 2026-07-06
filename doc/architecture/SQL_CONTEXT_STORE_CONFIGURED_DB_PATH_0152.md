# 0152 — SQLContextStore configured DB path

0152 moves the controlled SQL write smoke from a phase-local SQLite path toward a stable local SQL context store path.

The write path stays unchanged:

```text
0149 sql_context_store_persistence_record.json
-> SqlContextRecord
-> DbApiSqlContextStore.upsert_record
-> DB-API SQLite database
-> get_record readback
-> sql_context_store_controlled_write_result.json
```

Only database path resolution changes:

```text
--db-path
-> AUTODOC_SQL_CONTEXT_DB
-> .var/local/sql_context_store.sqlite3
```

Boundary:

- `src/context/sql_context_store.py` remains the authority surface.
- `DbApiSqlContextStore.upsert_record` remains the selected write method.
- The tool does not create a SQL worker, SQL orchestrator, or backend-specific client.
- SQL remains durable authority.
- Qdrant remains projection/recall only.
- OpenVINO and Qdrant backend clients are not imported.
- The Scheduler run loop is not modified.

This prepares a stable local P1 database while preserving the same DB-API injection seam for a future PostgreSQL connection.
