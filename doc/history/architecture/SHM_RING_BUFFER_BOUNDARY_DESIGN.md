# SHM ring buffer boundary design

Status: 0073 design only.

This document defines the boundary for the future real SHM transport. It does not implement it.

## Goal

The future implementation should replace the fake JSONL route files with a local hot path:

```text
/dev/shm/autodoc/
  event.bus
  context.bus
  data.index
  routes/<route_id>/
    ring
    notify
    status
```

## Boundary

The runtime schemas are already defined by phase 0065:

```text
missipy.shm.event_message.v1
missipy.shm.context_message.v1
missipy.shm.data_handle.v1
missipy.shm.route_message.v1
```

The real ring buffer must transport those logical messages, but it does not need to store pretty JSON internally.

## Suggested frame

A future frame should separate fixed header from payload:

```text
magic
version
schema_id
route_id_hash
message_id_hash
flags
payload_len
payload_hash
payload_bytes
```

## Ring behavior

Minimum future behavior:

```text
single producer / single consumer first
bounded capacity
monotonic write sequence
monotonic read sequence
payload hash validation
drop or block policy explicit
no silent overwrite
```

## Notification

Notification is separate from payload.

Future options:

```text
eventfd
futex
POSIX semaphore
pipe wakeup
io_uring later
```

The notification only wakes readers. The message remains in the ring.

## Safety rules

The real SHM layer must not decide security.

It must receive already-authorized/materialized routes from the passive RouteProxy.

```text
SecurityFS -> Scheduler -> ControlFS -> RouteProxy -> SHM Runtime
```

## Relationship with fake runtime

The fake runtime writes:

```text
data.index.jsonl
event.bus.jsonl
context.bus.jsonl
routes/<route_id>/messages.jsonl
```

The real runtime will replace the storage mechanism while keeping the same logical message schemas.

## Non-goals

This phase does not add:

```text
real shared memory implementation
mmap implementation
ring buffer code
eventfd code
futex code
semaphore code
RouteProxy daemon
Scheduler wiring
NetworkBridge
HardwareBridge
cluster dispatch
```

## Future implementation order

Recommended next implementation order:

```text
1. tiny in-process ring buffer model
2. file-backed mmap prototype in tmpfs
3. /dev/shm route directory prototype
4. eventfd or semaphore notification
5. RouteProxy materialization
6. Recorder tail/replay
```
