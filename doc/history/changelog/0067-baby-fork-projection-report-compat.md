# 0067 - Baby-fork projection report compatibility

## Fixed

- `variant_count` no longer stays at zero when variants are nested in the real report.
- Projection now emits `variant_ids`.
- Projection now uses a deterministic report SHA-256 in `DataHandle.hash`.

## Still not added

- No real shared memory.
- No semaphores.
- No ring buffer.
- No RouteProxy daemon.
- No Scheduler wiring.
- No ControlFS mutation.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
