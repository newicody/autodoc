# 0076 - In-process ring buffer model

## Added

- `runtime.inprocess_ring_buffer`
- `InProcessRingBuffer`
- `InProcessRouteRuntime`
- explicit overflow policies:
  - `reject`
  - `drop_oldest`
- monotonic slot sequence
- ring stats
- CLI tool `tools/replay_fake_routes_to_ring.py`
- tests for ordering, capacity and overflow
- rule tests locking model-only scope

## Not added

- No real shared memory.
- No mmap.
- No semaphores.
- No eventfd/futex.
- No RouteProxy daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No thread/process safety.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
