# mmap fixed-slot route prototype

Status: 0080 prototype.

This phase consumes the ControlProxy decision from `0079-r2` and materializes a
file-backed fixed-slot mmap route.

## Input

```text
RoutePrepareDecision(status=ready)
  route_handle
  slot_size
  slot_count
  max_frame_bytes
  overflow_policy
  notify
```

## Output

```text
<runtime_root>/routes/<route_handle>/ring.bin
<runtime_root>/routes/<route_handle>/status.json
```

Example:

```text
.var/mmap_runtime/routes/baby_fork.retrieval@g1/ring.bin
.var/mmap_runtime/routes/baby_fork.retrieval@g1/status.json
```

## Ring layout

```text
ring header 128 bytes
slot 0
slot 1
...
slot N
```

Each slot:

```text
slot header 64 bytes
fixed frame area slot_size bytes
```

The frame area contains one encoded `RouteMessage` frame from the phase 0077
codec.

## Write protocol

```text
validate frame
check frame_size <= slot_size
write slot header as EMPTY
write frame bytes
write slot header as COMMITTED
advance write_sequence
flush mmap
```

## Drain protocol

```text
check read_sequence slot
validate COMMITTED state
verify mirrored sequence
verify frame checksum
decode RouteMessage frame
mark slot EMPTY
advance read_sequence
flush mmap
```

## What this proves

```text
ControlProxy sizing decision
-> file-backed mmap route
-> fixed slot frame write
-> fixed slot frame drain
-> RouteMessage decode
```

## Non-goals

This phase does not add:

```text
POSIX shm_open
mandatory /dev/shm
semaphores
eventfd
futex
ControlProxy daemon
ControlFS watcher
Scheduler wiring
lease handoff
live mmap resize
inter-process safety
VisPy renderer
NetworkBridge
HardwareBridge
cluster dispatch
```

## No CLI

This patch intentionally does not add a new CLI.

The rule is:

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

The mmap prototype is still a runtime primitive, not yet an operator surface.

## Next

```text
0081 materialized active route status / ControlProxy active route writer
0082 notification layer
0083 Scheduler lease handshake
```
