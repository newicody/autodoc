# Code rule 0221 — Passive supervision uses EventBus as the main path

This rule locks the passive supervision direction before further functional work.

## Required direction

The canonical runtime path is:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
```

Snapshots and audit journals are optional outputs. They are not the runtime backbone.

## Authority boundary

The passive supervisor is downstream-only. It must not:

- call or modify `Scheduler.run()`;
- control RouteProxy or ControlProxy;
- read or write raw `/dev/shm` as a required path;
- decide policy;
- write SQL or Qdrant;
- mutate GitHub;
- dispatch tasks;
- become a worker or runtime authority.

## Reuse requirement

Before adding any new bus, bridge, adapter, scheduler source, proxy surface, or visualization module, audit existing code and prefer updating the existing passive supervisor/EventBus surfaces.

If an adapter is required, document why the existing EventBus contract cannot be consumed directly.
