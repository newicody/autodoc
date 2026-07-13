# Phase 0283-r7-r1 report — lazy SQL store import fix

## Diagnosis

The full suite had already registered a lightweight
`context.sql_context_store` module in `sys.modules`. The r7 CLI imported
`DbApiSqlContextStore` at module load time, so every readiness and projection
test failed before CLI gate evaluation.

The canonical repository module does expose `DbApiSqlContextStore` and
`SqlContextStorePolicy`. The failure was caused by eager loading in a process
whose test state already contained a stub, not by an absent production class.

## Correction

The CLI now imports the existing SQL store inside
`_open_read_only_sql_store()` only. That function is reached exclusively for an
authorized recall execute path after live readiness succeeds.

```text
sql_store_import_lazy: true
readiness_imports_sql_store: false
projection_imports_sql_store: false
recall_preview_imports_sql_store: false
recall_execute_imports_sql_store: true
```

## Boundaries

```text
runtime_behavior_changed: import timing only
scheduler_modified: false
new_runtime_module_added: false
new_transport_added: false
qdrant_effect_added: false
sql_write_added: false
projects_repository_change_required: false
```
