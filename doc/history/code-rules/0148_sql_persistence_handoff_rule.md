# Code rule 0148 — SQL persistence handoff only

0148 is handoff-only.

Required boundary:

- SQLContextStore remains durable authority.
- Qdrant remains projection/recall only.
- `src/context/sql_persistence_handoff_contract.py` may define a pure serializable contract.
- `tools/run_sql_persistence_handoff_smoke.py` may write local handoff JSON/Markdown artifacts.

Forbidden in 0148:

- must not create SQLPersistenceWorker.
- must not create SQLOrchestrator.
- must not import Qdrant or OpenVINO backends.
- must not write SQL rows directly.
- must not modify the Scheduler run loop.

The next patch may connect the handoff to the existing SQLContextStore through the established context authority surface.
