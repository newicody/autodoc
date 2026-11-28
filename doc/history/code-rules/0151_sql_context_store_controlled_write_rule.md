# Code rule 0151 — SQLContextStore controlled write

0151 may perform a real local SQL write only through the existing SQL context store authority surface.

Required boundary:

- `DbApiSqlContextStore.upsert_record` is the selected write method.
- `SqlContextRecord` is the record shape written to SQL.
- SQL remains durable authority.
- Qdrant remains projection/recall only.
- Qdrant identifiers may be persisted only as projection metadata.
- `tools/run_sql_context_store_controlled_write_smoke.py` may use a DB-API SQLite smoke database as an injected connection for the existing store.

Forbidden in 0151:

- must not create SQLPersistenceWorker.
- must not create SQLOrchestrator.
- must not create LocalArtifactOrchestrator.
- must not create LocalVectorIndexingOrchestrator.
- must not import OpenVINO backend clients.
- must not import Qdrant backend clients.
- must not modify the Scheduler run loop.
- must not make Qdrant the durable source of truth.

The smoke must write and read back through `DbApiSqlContextStore`, not through a parallel SQL API.
