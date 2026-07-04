# 0066 - Baby-fork runtime message projection

## Added

- `context.baby_fork_runtime_projection`
- `BabyForkRuntimeProjection`
- projection from baby-fork report to:
  - `DataHandle`
  - `EventBusMessage`
  - `ContextBusMessage`
  - `RouteMessage`
- CLI tool `tools/export_baby_fork_runtime_projection.py`
- documentation for baby-fork runtime projection
- tests for projected route IDs and message schemas
- rule tests locking adapter-only scope

## Not added

- No change to baby-fork core pipeline.
- No real shared memory.
- No semaphores.
- No ring buffer.
- No RouteProxy daemon.
- No Scheduler wiring.
- No ControlFS mutation.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
