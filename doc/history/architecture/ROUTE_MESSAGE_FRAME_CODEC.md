# RouteMessage frame codec

Status: 0077 codec only.

This phase adds a byte-level frame codec for validated `RouteMessage` payloads.

It is not shared memory. It is not `mmap`. It is not a ring buffer implementation.

## Goal

Prepare the future SHM transport by proving this transformation:

```text
RouteMessage object
-> deterministic payload bytes
-> binary frame
-> decode
-> validated RouteMessage object
```

## Frame header

The first frame version uses a fixed header:

```text
magic          8 bytes
version        uint16
flags          uint16
header_size    uint32
payload_size   uint32
payload_sha256 32 bytes
```

Payload is canonical JSON for now.

The binary wrapper already checks:

```text
magic
version
header size
frame length
payload SHA-256
RouteMessage schema validation
```

## CLI

```bash
PYTHONPATH=src:. python tools/roundtrip_route_frame.py \
  .var/baby_fork_fake_runtime \
  --route-id baby_fork.variant_stub
```

## Relationship to the ring model

Phase 0076 models ring behavior with Python objects.

Phase 0077 models the byte frame that a future ring can store.

The future ring can later move from object slots to byte frames.

## Non-goals

This phase does not add:

```text
real shared memory
mmap
semaphores
eventfd
futex
ring buffer implementation
RouteProxy daemon
ControlFS watcher
Scheduler wiring
zero-copy transport
NetworkBridge
HardwareBridge
cluster dispatch
```

## Future implementation path

Recommended next steps:

```text
1. integrate frame codec with in-process ring model
2. add frame size limits
3. add byte capacity accounting
4. then prototype mmap file-backed ring
5. then move to /dev/shm route directories
```
