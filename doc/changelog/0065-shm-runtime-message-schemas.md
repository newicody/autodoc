# 0065 - SHM Runtime message schemas

## Added

- `runtime.shm_runtime_schema`
- `DataHandle`
- `EventBusMessage`
- `ContextBusMessage`
- `RouteMessage`
- `parse_runtime_json`
- CLI validator `tools/validate_shm_runtime_message.py`
- documentation for SHM Runtime schemas
- functional tests for valid and invalid schema objects
- rule tests locking schema-only scope

## Not added

- No real shared memory.
- No semaphores.
- No ring buffer.
- No RouteProxy daemon.
- No Scheduler wiring.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
