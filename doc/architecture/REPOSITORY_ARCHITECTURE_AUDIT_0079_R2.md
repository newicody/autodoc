# Repository architecture audit - 0079-r2

Scope: repository reconstructed from applied patches `0063-r2` through `0078`.

This audit replaces the rejected old `0079`.

## Current executable runtime pieces

```text
src/runtime/controlfs_manifest.py
src/runtime/routeproxy_reconciler.py
src/runtime/shm_runtime_schema.py
src/runtime/fake_route_transport.py
src/runtime/fake_runtime_recorder.py
src/runtime/inprocess_ring_buffer.py
src/runtime/route_frame_codec.py
src/runtime/inprocess_frame_ring.py
```

## Current context pieces

```text
src/context/baby_fork_runtime_projection.py
src/context/baby_fork_controlfs.py
src/context/baby_fork_runtime_flow.py
```

## Gap closed by 0079-r2

```text
ControlProxy unit vocabulary.
Route prepare request/status protocol.
Route sizing as part of ControlProxy, not separate ControlFS-only logic.
Bus projection for ControlProxy state.
Visibility for VisPy/Cell Lens via event.bus/context.bus.
Timing-budget contract for route preparation.
Documentation of requested -> ready -> leased -> active flow.
Repository architecture audit/index before mmap.
```

## Still open after 0079-r2

```text
file-backed fixed-slot mmap route
materialized active route directories
route generation lease handoff
semaphore/eventfd notification
real ControlProxy watcher/daemon
Scheduler integration
VisPy renderer adapter
Recorder category rules for ControlProxy events
NetworkBridge
HardwareBridge
cluster dispatch
```

## Required order

```text
0079-r2 ControlProxy sizing + prepare + bus
0080 file-backed fixed-slot mmap route
0081 materialize active route status from mmap route
0082 notification layer
0083 Scheduler lease handshake
0084 VisPy adapter
```
