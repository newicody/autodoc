# Manifest — 0271-r3 qdrant-client live projection/recall binding

## Modified existing surfaces

- `tools/run_scheduler_managed_embedding_qdrant_projection_0262.py`
- `tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py`
- `src/context/production_prototype_smoke_composition_0269.py`
- `tools/run_production_prototype_smoke_composition_0269.py`

## Added phase surfaces

- `tests/context/test_qdrant_client_live_projection_recall_binding_0271.py`
- `tests/rules/test_qdrant_client_live_projection_recall_binding_0271_rule.py`
- `doc/architecture/QDRANT_CLIENT_LIVE_PROJECTION_RECALL_BINDING_0271.md`
- `doc/code-rules/0271_qdrant_client_live_projection_recall_binding_rule.md`
- `doc/CHANGELOG_0271_QDRANT_CLIENT_LIVE_PROJECTION_RECALL_BINDING.md`
- `doc/docs/architecture/runtime/271_qdrant_client_live_projection_recall_binding.dot`
- `PHASE0271_QDRANT_CLIENT_LIVE_PROJECTION_RECALL_BINDING_TEST_REPORT.md`

No Scheduler, SHM, service manager or collection-creation surface is changed.
