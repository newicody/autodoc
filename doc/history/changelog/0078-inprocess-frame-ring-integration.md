# 0078 - In-process frame ring integration

## Added

- `runtime.inprocess_frame_ring`
- `InProcessFrameRingBuffer`
- `InProcessFrameRouteRuntime`
- storage of encoded `RouteMessage` frames
- decode-on-read validation
- frame byte stats
- optional `max_frame_bytes`
- CLI `tools/replay_fake_routes_to_frame_ring.py`
- tests for frame storage, decoding, overflow and max frame size
- rule tests locking in-process-only scope

## Not added

- No real shared memory.
- No mmap.
- No semaphores.
- No eventfd/futex.
- No RouteProxy daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No zero-copy transport.
- No thread/process safety.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
