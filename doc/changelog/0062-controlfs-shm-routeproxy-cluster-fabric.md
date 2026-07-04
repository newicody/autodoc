# 0062 - ControlFS / SHM / RouteProxy / Cluster Fabric architecture

## Added

- Locked runtime architecture document for:
  - SecurityFS
  - Scheduler
  - ControlFS
  - passive RouteProxy
  - SHM Runtime
  - DataHandle
  - Recorder
  - ZFS Store
  - future NetworkBridge
  - distant future Hardware Cluster Fabric
- Priority plan for the next development tasks.
- ADR-0062 documenting the decision.
- Rule tests checking the locked phrases and future-only boundaries.

## Changed

- Replaces the old mental model `Gateway/Proxy -> Scheduler` with:
  - `Scheduler -> ControlFS desired state`
  - `RouteProxy watches ControlFS`
  - `RouteProxy materializes shm routes and semaphores`

## Not implemented

- No Scheduler code change.
- No RouteProxy daemon.
- No real shm rings.
- No semaphores.
- No NetworkBridge.
- No HardwareBridge.
- No FPGA/ASIC integration.
- No distributed cluster dispatch.
