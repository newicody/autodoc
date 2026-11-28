# In-process frame ring integration

Status: 0078 in-process integration only.

This phase integrates:

```text
0076 InProcessRingBuffer behavior
0077 RouteMessage frame codec
```

The new frame ring stores bytes frames, not Python `RouteMessage` objects.

## Goal

Prove the path:

```text
RouteMessage
-> binary RouteMessage frame
-> in-process bounded frame ring
-> drain
-> decode
-> validated RouteMessage
```

before implementing `mmap` or `/dev/shm`.

## What the frame ring tracks

```text
capacity
occupancy
total_frame_bytes
max_frame_bytes
write_sequence
read_sequence
dropped_count
overflow_policy
```

## Overflow policies

```text
reject
drop_oldest
```

There is still no silent overwrite.

## CLI

```bash
PYTHONPATH=src:. python tools/replay_fake_routes_to_frame_ring.py \
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
zero-copy transport
thread/process safety
NetworkBridge
HardwareBridge
cluster dispatch
```

## Future implementation path

Next steps:

```text
1. add byte capacity accounting per route
2. add fixed-size frame slot constraints
3. prototype file-backed mmap ring in tmpfs
4. move route directory layout to /dev/shm/autodoc
5. add notification layer separately
```
