# 0077 - RouteMessage frame codec

## Added

- `runtime.route_frame_codec`
- fixed binary frame header
- deterministic RouteMessage JSON payload
- SHA-256 payload validation
- decode-time RouteMessage schema validation
- CLI `tools/roundtrip_route_frame.py`
- tests for roundtrip, corruption and schema rejection
- rule tests locking codec-only scope

## Not added

- No real shared memory.
- No mmap.
- No semaphores.
- No eventfd/futex.
- No ring buffer implementation.
- No RouteProxy daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No zero-copy transport.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
