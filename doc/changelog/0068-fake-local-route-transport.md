# 0068 - Fake local route transport

## Added

- `runtime.fake_route_transport`
- `FakeLocalRouteTransport`
- fake JSONL layout for:
  - `data.index`
  - `event.bus`
  - `context.bus`
  - `routes/<route_id>`
- CLI tool `tools/write_baby_fork_fake_runtime.py`
- documentation for fake local route transport
- tests validating baby-fork projection can be written to fake runtime
- rule tests locking fake-only scope

## Not added

- No real shared memory.
- No semaphores.
- No ring buffer.
- No eventfd/futex.
- No RouteProxy daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
