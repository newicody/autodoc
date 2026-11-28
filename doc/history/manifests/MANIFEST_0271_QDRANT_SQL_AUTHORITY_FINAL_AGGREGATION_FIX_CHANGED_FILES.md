# Manifest — 0271-r6 Qdrant SQL-authority final aggregation fix

## Modified

- `tools/run_production_prototype_smoke_composition_0269.py`

## Added

- `tests/tools/test_qdrant_sql_authority_final_aggregation_0271.py`
- `tests/rules/test_qdrant_sql_authority_final_aggregation_0271_rule.py`
- `doc/architecture/QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX_0271.md`
- `doc/code-rules/0271_qdrant_sql_authority_final_aggregation_fix_rule.md`
- `doc/docs/architecture/runtime/271_qdrant_sql_authority_final_aggregation_fix.dot`
- `doc/CHANGELOG_0271_QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX.md`
- `doc/manifests/MANIFEST_0271_QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX_CHANGED_FILES.md`
- `PHASE0271_QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX_TEST_REPORT.md`

## Explicitly unchanged

- Scheduler and its loop;
- 0262 projection and 0263 recall tools;
- Qdrant executor and SQL-authority membrane;
- SHM, RouteProxy and ControlProxy;
- OpenRC and external-service lifecycle.
