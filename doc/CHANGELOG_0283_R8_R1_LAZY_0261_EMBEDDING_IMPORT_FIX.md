# Changelog 0283-r8-r1 — lazy 0261 embedding import fix

- Removed the 0261 import from smoke module initialization.
- Added one lazy resolver for the existing request, runner and demo builder.
- Required injected embedding test surfaces to be supplied as a complete group.
- Added a regression test with a pre-existing 0261 `sys.modules` stub.
- Preserved preview and execute behavior.
- Added no embedding implementation, runtime component, transport or effect.

```text
embedding_0261_import_lazy: true
canonical_0261_runtime_reused: true
injected_tests_import_0261: false
embedding_runtime_duplicated: false
preview_effects_changed: false
execute_effects_changed: false
scheduler_modified: false
new_runtime_module_added: false
new_transport_added: false
qdrant_effect_added: false
sql_write_added: false
projects_repository_change_required: false
```
