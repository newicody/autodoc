# 0075 - Fake runtime replace semantics

## Fixed

- Repeated fake runtime writes no longer accumulate route messages by default.
- End-to-end baby-fork runtime flow remains deterministic:
  - `route_message_count = 3`
  - `record_count = 7`
- `tools/write_baby_fork_fake_runtime.py` now has `--append-routes` for explicit append behavior.

## Not added

- No real shared memory.
- No semaphores.
- No ring buffer.
- No RouteProxy daemon.
- No Scheduler wiring.
- No ControlFS mutation.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
