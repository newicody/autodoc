# Changelog 0282-r8 — ProjectV2 real cycle-history smoke

- Added one deterministic r4→r5→r6 composition contract.
- Added one CLI that reuses the existing r7 adapter.
- Kept preview as the default mode.
- Required the exact preview smoke digest before execution.
- Forwarded exact r5/r6 plan digests to r7 automatically.
- Added stable JSON artifacts for review and replay.
- Propagated partial remote execution honestly.
- Added no Scheduler, mutation transport, SQL writer or Qdrant writer.

```text
existing_r7_adapter_reused: true
preview_is_default: true
exact_smoke_digest_required_for_execution: true
new_scheduler_added: false
new_mutation_transport_added: false
sql_write_added: false
qdrant_write_added: false
projects_repository_change_required: false
external_dependencies_added: false
```
