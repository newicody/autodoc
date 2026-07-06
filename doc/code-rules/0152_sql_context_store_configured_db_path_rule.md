# Code rule 0152 — SQLContextStore configured DB path

0152 may stabilize the local SQL database path, but it must keep the existing SQL authority surface.

Required boundary:

- `DbApiSqlContextStore.upsert_record` remains the selected write method.
- `SqlContextRecord` remains the durable record shape.
- DB path precedence is `--db-path`, then `AUTODOC_SQL_CONTEXT_DB`, then `.var/local/sql_context_store.sqlite3`.
- SQL remains durable authority.
- Qdrant remains projection/recall only.
- Qdrant identifiers may be persisted only as projection metadata.

Forbidden in 0152:

- must not create SQLPersistenceWorker.
- must not create SQLOrchestrator.
- must not create LocalArtifactOrchestrator.
- must not create LocalVectorIndexingOrchestrator.
- must not import OpenVINO backend clients.
- must not import Qdrant backend clients.
- must not modify the Scheduler run loop.
- must not make Qdrant the durable source of truth.

0152 only changes connection path selection for the existing DB-API SQLContextStore write smoke.
