# Changelog 0283-r5 — Qdrant controlled Scheduler recall binding

- Added one immutable command/policy/result surface around existing 0263.
- Reused the existing r3 scoped executor only in execute mode.
- Kept preview free of client construction, Qdrant search and SQL reads.
- Derived the default query reference through the existing 0263 helper.
- Required recall-only effect permissions by default.
- Bounded recall limit by the configured policy.
- Preserved reference-only hits before SQL rehydration.
- Closed the scoped binding after every constructed execution path.
- Added no Scheduler, executor, transport, proxy, bus or SHM/MMIO path.

```text
architecture_preserved: true
existing_0263_usage_reused: true
existing_r3_factory_reused: true
existing_sql_store_reused: true
preview_constructs_client: false
preview_reads_sql: false
qdrant_search_requires_execute: true
qdrant_returns_refs_only: true
sql_remains_authority: true
new_scheduler_added: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```
