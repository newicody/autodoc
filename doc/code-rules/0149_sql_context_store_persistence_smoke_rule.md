# Code rule 0149 — SQLContextStore persistence smoke

0149 may connect the 0148 SQL handoff to SQLContextStore as a typed persistence record.

Required boundary:

- SQLContextStore remains durable authority.
- Qdrant remains projection/recall only.
- `src/context/sql_context_store_persistence_contract.py` may define pure serializable contracts.
- `tools/run_sql_context_store_persistence_smoke.py` may inspect the existing SQLContextStore source and write local persistence-record artifacts.

Forbidden in 0149:

- must not create SQLPersistenceWorker.
- must not create SQLOrchestrator.
- must not create LocalArtifactOrchestrator.
- must not create LocalVectorIndexingOrchestrator.
- must not import OpenVINO or Qdrant backend clients.
- must not use backend-specific SQL client calls.
- must not modify the Scheduler run loop.

The next patch may bind the record to a concrete existing SQLContextStore method if the surface is explicit enough.
