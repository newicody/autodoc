# ADR-0062: ControlFS, passive RouteProxy, SHM Runtime and future cluster fabric

## Status

Accepted for architecture documentation.

## Context

The earlier Gateway/Proxy model was too direct and did not represent the desired runtime shape.

The corrected architecture says:

- Scheduler should not be called directly by a proxy.
- RouteProxy should be outside the Scheduler and passive.
- RouteProxy should observe a Unix filesystem state surface.
- RouteProxy should create/delete shared memory routes and semaphores.
- Scheduler should read/compile security rules and write desired route state.
- Runtime traffic should use `/dev/shm` routes, context/event buses and data handles.
- Persistent memory should go through Recorder and ZFS.
- Future network and hardware cluster concepts should be kept in the roadmap, not implemented now.

## Decision

Adopt the following runtime architecture:

```text
SecurityFS -> Scheduler -> ControlFS -> RouteProxy -> SHM Runtime -> Workers
                                             |
                                             v
                                      event/context/data handles
                                             |
                                             v
                                      Recorder -> ZFS -> Cell Lens
```

Future-only extensions:

```text
SHM Runtime -> NetworkBridge -> remote SHM Runtime
SHM Runtime -> PCIe HardwareBridge -> FPGA/ASIC Cluster Fabric -> remote machine
```

## Consequences

Good:

- Scheduler is not a throughput bottleneck.
- RouteProxy is a simple materializer, not a policy engine.
- ControlFS gives a clear Unix-native surface for route state.
- SHM Runtime gives a fast local path.
- ZFS keeps durable truth and replay.
- Network/hardware extensions remain possible without polluting V0.

Tradeoffs:

- More surfaces must be named clearly.
- ControlFS and SHM Runtime must not be confused.
- Low-level IPC must be delayed until schemas and dry-run behavior are stable.
- Hardware fabric is powerful but overkill for current smoke tests.

## Non-goals

This ADR does not implement:

- real shared memory rings
- semaphores
- NetworkBridge
- HardwareBridge
- FPGA/ASIC integration
- cluster dispatch
- Scheduler spawn changes

## Locked statements

```text
Scheduler writes desired route state into ControlFS.
RouteProxy passively watches ControlFS.
RouteProxy creates/deletes shm routes and semaphores.
RouteProxy does not call Scheduler.
RouteProxy does not decide security.
ControlFS is declarative state, not the hot bus.
SHM Runtime is the local fast path.
ZFS is durable memory.
NetworkBridge is future.
Hardware Cluster Fabric is future lointain.
```
