# 0074 - Baby-fork runtime flow CLI

## Added

- `context.baby_fork_runtime_flow`
- `tools/run_baby_fork_runtime_flow.py`
- end-to-end flow from baby-fork report to fake runtime and recorder journal
- optional ControlFS desired manifest + RouteProxy dry-run plan step
- tests for the complete file-backed flow
- rule tests locking no-real-runtime scope

## Not added

- No real Scheduler run.
- No RouteProxy daemon.
- No real shared memory.
- No semaphores.
- No ring buffer.
- No active route creation.
- No revoked route mutation.
- No ZFS requirement.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
