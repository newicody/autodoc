# 0071-0073 - ControlFS baby-fork manifests, RouteProxy plan, SHM ring design

## 0071 added

- Baby-fork ControlFS desired route manifests.
- `context.baby_fork_controlfs`
- `tools/write_baby_fork_controlfs_desired.py`

## 0072 added

- Baby-fork RouteProxy dry-run plan helper.
- `tools/baby_fork_routeproxy_plan.py`

## 0073 added

- SHM ring buffer boundary design document.
- Explicit non-implementation guardrails.

## Not added

- No real shared memory.
- No mmap implementation.
- No ring buffer code.
- No eventfd/futex/semaphore code.
- No RouteProxy daemon.
- No Scheduler wiring.
- No active route creation.
- No ControlFS watcher.
- No NetworkBridge.
- No HardwareBridge.
- No cluster dispatch.
