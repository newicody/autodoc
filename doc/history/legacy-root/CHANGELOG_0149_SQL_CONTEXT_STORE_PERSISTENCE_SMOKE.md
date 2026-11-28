# Changelog 0149 — SQLContextStore persistence smoke

Added:

- `src/context/sql_context_store_persistence_contract.py`
- `tools/run_sql_context_store_persistence_smoke.py`
- SQLContextStore persistence smoke tests and code-rule tests
- architecture/code-rule docs

0149 consumes the 0148 SQL handoff and builds a durable SQLContextStore persistence record. It does not invent a SQL worker, does not call Qdrant/OpenVINO, and does not guess a database-specific API.
