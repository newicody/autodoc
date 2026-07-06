# 0151 — SQLContextStore controlled write smoke

0151 performs the first real SQLContextStore write in the local artifact vector indexing chain.

The path becomes:

```text
0149 sql_context_store_persistence_record.json
-> SqlContextRecord
-> DbApiSqlContextStore.upsert_record
-> sql_context_records table in a DB-API SQLite smoke database
-> readback by context_ref
-> sql_context_store_controlled_write_result.json
```

Boundary:

- The existing `src/context/sql_context_store.py` surface is reused.
- The selected store class is `DbApiSqlContextStore`.
- The selected write method is `upsert_record`.
- The tool writes through an injected DB-API SQLite smoke database.
- SQL remains durable authority.
- Qdrant remains projection/recall only; Qdrant ids are metadata in the SQL record body/metadata.
- OpenVINO and Qdrant backend clients are not imported.
- The Scheduler run loop and RouteProxy runtime behavior are not modified.

0151 is intentionally a controlled smoke write. A later patch may switch the database connection source from the local SQLite smoke file to the production SQL connection factory already authorized by the project.
