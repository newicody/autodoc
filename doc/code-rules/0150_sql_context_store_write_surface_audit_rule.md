# Code rule 0150 — SQLContextStore write surface audit

0150 may audit the existing SQLContextStore source and prepare a write-surface decision.

Required boundary:

- SQLContextStore remains durable authority.
- Qdrant remains projection/recall only.
- `src/context/sql_context_store_write_surface_contract.py` may define pure serializable audit contracts.
- `tools/run_sql_context_store_write_surface_audit.py` may inspect `src/context/sql_context_store.py` and write local audit artifacts.
- `write_attempted` must remain false in 0150.

Forbidden in 0150:

- must not create SQLPersistenceWorker.
- must not create SQLOrchestrator.
- must not create LocalArtifactOrchestrator.
- must not create LocalVectorIndexingOrchestrator.
- must not import OpenVINO or Qdrant backend clients.
- must not import backend-specific SQL clients.
- must not modify the Scheduler run loop.

If no explicit SQLContextStore write method is present, 0150 must report `blocked_no_explicit_sql_context_store_write_method` rather than guessing an API.
