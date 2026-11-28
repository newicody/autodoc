# 0080 - mmap fixed-slot route prototype

## Added

- `runtime.mmap_fixed_slot_route`
- file-backed `ring.bin`
- fixed slot header + fixed frame area
- route status JSON
- write encoded RouteMessage frames
- drain encoded RouteMessage frames
- checksum validation
- ControlProxy decision materialization helper
- tests for:
  - file sizing
  - materialization from ControlProxy decision
  - write/drain/decode
  - frame-too-large rejection
  - full-ring rejection
  - drop-oldest mode
  - status file
  - rule docs

## Not added

- No POSIX `shm_open`.
- No mandatory `/dev/shm`.
- No semaphores/eventfd/futex.
- No daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No lease handoff.
- No live resize.
- No inter-process safety.
- No CLI.

## Compatibility

Validated after `0079-r3` rule phrase compatibility.
