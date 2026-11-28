# Changelog 0151 — SQLContextStore controlled write

Added:

- `src/context/sql_context_store_controlled_write_contract.py`
- `tools/run_sql_context_store_controlled_write_smoke.py`
- controlled write tests and code-rule tests
- architecture/code-rule docs

0151 consumes the 0149 SQLContextStore persistence record, converts it into a `SqlContextRecord`, writes it through `DbApiSqlContextStore.upsert_record`, and reads it back from the smoke database.
