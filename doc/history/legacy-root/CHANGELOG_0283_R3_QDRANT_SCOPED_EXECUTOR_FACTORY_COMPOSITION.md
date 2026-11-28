# Changelog 0283-r3 — Qdrant scoped executor factory composition

- Added one composition factory around the existing qdrant-client builder.
- Wrapped every constructed delegate immediately with the existing SQL scope.
- Added dependency-readiness validation before construction.
- Added optional API-key environment resolution at the I/O boundary.
- Added a secret-free serializable construction report.
- Preserved the existing effect gate without issuing projection or recall.
- Added no alternate transport, Scheduler route, proxy route, bus route or SHM route.

```text
architecture_preserved: true
existing_client_factory_reused: true
existing_concrete_executor_reused: true
existing_sql_scope_wrapper_reused: true
new_qdrant_executor_added: false
new_transport_added: false
scheduler_modified: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
qdrant_write_performed: false
qdrant_search_performed: false
projects_repository_change_required: false
external_dependencies_added: false
```
