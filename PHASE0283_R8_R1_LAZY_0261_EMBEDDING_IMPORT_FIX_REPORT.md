# Phase 0283-r8-r1 report — lazy 0261 embedding import fix

## Diagnosis

The complete suite had already registered a lightweight
`context.scheduler_managed_sql_ref_openvino_embedding_usage_0261` module in
`sys.modules`. The r8 smoke imported its request and functions during module
initialization, so every smoke test failed before gate evaluation.

The canonical 0261 module does expose:

```text
SchedulerManagedSqlRefOpenVinoEmbeddingRequest
build_demo_embedding
run_scheduler_managed_sql_ref_openvino_embedding_usage
```

The failure was process-global test-state contamination, not a missing
production contract.

## Correction

The smoke now resolves the canonical 0261 trio lazily. Production usage with no
injection imports and reuses the existing 0261 implementation. Tests that
inject an embedding runner must inject the matching request builder and demo
builder as one complete group; they never import the contaminated module.

```text
embedding_0261_import_lazy: true
canonical_0261_runtime_reused: true
injected_tests_import_0261: false
embedding_runtime_duplicated: false
```

## Boundaries

```text
preview_effects_changed: false
execute_effects_changed: false
scheduler_modified: false
new_runtime_module_added: false
new_transport_added: false
qdrant_effect_added: false
sql_write_added: false
projects_repository_change_required: false
```
