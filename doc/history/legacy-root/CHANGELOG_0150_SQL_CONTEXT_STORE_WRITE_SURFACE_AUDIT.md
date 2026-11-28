# Changelog 0150 — SQLContextStore write surface audit

Added:

- `src/context/sql_context_store_write_surface_contract.py`
- `tools/run_sql_context_store_write_surface_audit.py`
- SQLContextStore write-surface audit tests and code-rule tests
- architecture/code-rule docs

0150 consumes the 0149 persistence record and audits the existing SQLContextStore-compatible class for an explicit write method. It remains audit-only and performs no backend write.


0150-r1 also recognizes `DbApiSqlContextStore.upsert_record` as the existing explicit write surface when the repository exposes that name instead of a class named exactly `SQLContextStore`.
