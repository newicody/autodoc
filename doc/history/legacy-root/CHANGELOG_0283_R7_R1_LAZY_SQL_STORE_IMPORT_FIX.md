# Changelog 0283-r7-r1 — lazy SQL store import fix

- Removed the SQL store import from CLI module initialization.
- Imported the existing SQL store only when opening the read-only recall store.
- Added a regression test with a pre-existing `sys.modules` stub.
- Preserved all preview, readiness and authorization behavior.
- Added no runtime component, transport or data effect.

```text
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
