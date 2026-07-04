# In-process ring buffer model

Status: 0076 model only.

This phase introduces a tiny in-process ring buffer model for validated `RouteMessage` objects.

It is not `/dev/shm`. It is not `mmap`. It is not a daemon.

## Goal

Test the future ring-buffer rules before touching kernel IPC:

```text
bounded capacity
FIFO ordering
monotonic sequence
explicit overflow behavior
no silent overwrite
validated RouteMessage at boundary
```

## Overflow policies

Supported policies:

```text
reject
drop_oldest
```

`reject` raises an explicit overflow error.

`drop_oldest` explicitly drops the oldest unread slot and increments `dropped_count`.

There is no silent overwrite.

## Route runtime model

The route runtime is a route registry:

```text
route_id -> InProcessRingBuffer
```

It accepts only validated `missipy.shm.route_message.v1` messages.

## CLI

```bash
PYTHONPATH=src:. python tools/replay_fake_routes_to_ring.py \
  .var/baby_fork_fake_runtime \
  --capacity 4
```

## Non-goals

This phase does not add:

```text
real shared memory
mmap
semaphores
eventfd
futex
RouteProxy daemon
ControlFS watcher
Scheduler wiring
thread/process safety
NetworkBridge
HardwareBridge
cluster dispatch
```

## Future implementation path

Next steps:

```text
1. keep this model as behavioral reference
2. add byte-frame codec for RouteMessage
3. test frame encode/decode independently
4. then build file-backed mmap prototype in tmpfs
5. then move to /dev/shm route directories
```
