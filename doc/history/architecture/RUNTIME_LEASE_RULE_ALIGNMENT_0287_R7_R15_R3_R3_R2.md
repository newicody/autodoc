# Runtime lease rule alignment

The runtime lease remains a domain ownership contract. It may compare process
identities supplied by its caller, but it does not discover those identities.

```text
CLI adapter
  └─ os.getpid()
       ├─ acquire_imported_actions_runtime_lease(
       │    current_process_id=...)
       └─ ImportedActionsRuntimeLease.close(
            current_process_id=...)

domain contract
  ├─ validates creator process_id
  ├─ validates current_process_id
  ├─ rejects mismatches
  └─ never imports os
```

After acquisition the preview tool explicitly validates `runtime_lease.ports`
through the existing `validate_imported_actions_runtime_ports` function. The
lease is therefore an ownership wrapper, not a replacement for the historical
runtime-port gate.

The Scheduler remains the sole orchestrator. The tool starts and stops it only
for the already-declared `tool-bounded` lifecycle. SQL remains durable
authority, Qdrant remains a reference projection/recall surface, and OpenVINO
E5 remains a 384-dimensional injected backend.
