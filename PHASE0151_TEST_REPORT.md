# PHASE0151_TEST_REPORT

```text
phase: 0151-sql_context_store_controlled_write
code_rule_review: done
code_rule_update_required: true
code_rule_reason: Real SQL persistence must go through DbApiSqlContextStore.upsert_record and keep Qdrant as projection metadata only.
live_path_status: controlled_sql_context_store_write
live_path_uses_real_backend: sqlite_smoke_dbapi
context_contract_version: sql-context-store-controlled-write-0151
context_contract_changed: true
search_commands_bounded: n/a
```

Validation performed in patch build:

```bash
PYTHONPATH=src:. python -m compileall -q src tests tools
PYTHONPATH=src:. pytest -q tests/tools/test_sql_context_store_controlled_write_smoke_0151.py tests/rules/test_sql_context_store_controlled_write_smoke_0151_rule.py
# expected: 8 passed
```
