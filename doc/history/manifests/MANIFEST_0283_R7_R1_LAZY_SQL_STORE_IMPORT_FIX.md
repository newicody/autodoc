# Manifest 0283-r7-r1 — lazy SQL store import fix

## Modified

```text
tools/run_qdrant_real_binding_0283.py
tests/tools/test_run_qdrant_real_binding_0283.py
```

## Added

```text
tests/rules/test_qdrant_real_binding_cli_lazy_sql_store_import_0283_rule.py
doc/manifests/MANIFEST_0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX.md
doc/CHANGELOG_0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX.md
PHASE0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX_REPORT.md
```

## Impact

```text
Repo autodoc: OUI
Repo projects: NON
sql_store_import_lazy: true
readiness_imports_sql_store: false
projection_imports_sql_store: false
recall_preview_imports_sql_store: false
recall_execute_imports_sql_store: true
scheduler_modified: false
new_runtime_module_added: false
new_transport_added: false
qdrant_effect_added: false
sql_write_added: false
projects_repository_change_required: false
```
