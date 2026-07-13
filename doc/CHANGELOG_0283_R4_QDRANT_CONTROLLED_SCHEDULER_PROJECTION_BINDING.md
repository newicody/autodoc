# Changelog 0283-r4 — Qdrant controlled Scheduler projection binding

- Added one immutable command/policy/result surface around the existing 0262
  projection use case.
- Reused the existing r3 scoped executor factory only in execute mode.
- Kept preview client-free and write-free.
- Built the 0262 request directly from the validated r2 target and decision.
- Required a projection-only effect gate by default.
- Rejected non-default projection policy until 0262 accepts an injected policy.
- Closed the scoped binding after every constructed execution path.
- Added no Scheduler, transport, proxy, bus, SHM or MMIO path.

```text
architecture_preserved: true
existing_0262_usage_reused: true
existing_r3_factory_reused: true
preview_constructs_client: false
qdrant_write_requires_execute: true
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
