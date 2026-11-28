# Manifest — 0271-r5 SQL-authority scope live binding

## Modified existing surfaces

- `tools/run_scheduler_managed_embedding_qdrant_projection_0262.py`
- `tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py`
- `src/context/production_prototype_smoke_composition_0269.py`
- `tools/run_production_prototype_smoke_composition_0269.py`
- `tests/context/test_qdrant_client_live_projection_recall_binding_0271.py`

## Added tests

- `tests/context/test_qdrant_sql_authority_scope_live_binding_0271.py`
- `tests/rules/test_qdrant_sql_authority_scope_live_binding_0271_rule.py`

## Added documentation

- `doc/architecture/QDRANT_SQL_AUTHORITY_SCOPE_LIVE_BINDING_0271.md`
- `doc/code-rules/0271_qdrant_sql_authority_scope_live_binding_rule.md`
- `doc/docs/architecture/runtime/271_qdrant_sql_authority_scope_live_binding.dot`
- `doc/CHANGELOG_0271_QDRANT_SQL_AUTHORITY_SCOPE_LIVE_BINDING.md`
- `PHASE0271_QDRANT_SQL_AUTHORITY_SCOPE_LIVE_BINDING_TEST_REPORT.md`

No new manager, worker, orchestrator, service controller or SHM surface is added.
