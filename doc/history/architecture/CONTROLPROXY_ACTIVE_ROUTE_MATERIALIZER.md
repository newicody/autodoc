# ControlProxy active route materializer

Status: 0081 implementation bridge.

This phase starts moving from prototype pieces toward the real implementation
shape.

## Vocabulary

```text
ControlProxy = ControlFS declarative surface + RouteProxy materializer
```

## Purpose

`0080-r2` can create a file-backed fixed-slot mmap route, but the route is not
yet connected to ControlFS active state.

`0081` connects:

```text
ControlProxy RoutePrepareDecision
+ desired RouteManifest
-> mmap route files
-> ControlFS active/routes/<route_id>/manifest.json
-> ControlFS active/routes/<route_id>/status.json
```

## Surfaces

Runtime mmap surface:

```text
<runtime_root>/routes/<route_handle>/ring.bin
<runtime_root>/routes/<route_handle>/status.json
```

ControlFS active surface:

```text
<controlfs_root>/active/routes/<route_id>/manifest.json
<controlfs_root>/active/routes/<route_id>/status.json
```

The active manifest is a valid `RouteManifest` copy of the accepted desired
manifest. This keeps the dry-run reconciler compatible: if desired and active
match, the route can plan as `noop`.

## Active status

Schema:

```text
missipy.controlproxy.active_route_status.v1
```

Fields include:

```text
route_id
route_handle
task_id
zone
state
implementation_stage
runtime_route_dir
ring_path
mmap_status_path
active_manifest_path
active_status_path
slot_size
slot_count
max_frame_bytes
notify
overflow_policy
route_ready_at
lease_state
```

Initial lease state:

```text
not_leased
```

## Real implementation path

This is the seam for the real ControlProxy materializer.

Later phases should replace the current direct function call with an
explicitly called pump/tick, not a service:

```text
ControlProxy pump/tick
-> reads ControlFS desired/request state when called
-> materializes runtime routes
-> writes active state
-> publishes bus facts
```

The API and files should remain stable. No OpenRC service and no resident daemon
are planned for this path.

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
route lease issuing
lease handoff
live mmap resize
inter-process safety
VisPy renderer
NetworkBridge
HardwareBridge
cluster dispatch
```

## No CLI

This patch intentionally does not add a CLI.

The rule remains:

```text
module logic is importable
tests validate behavior
CLI only when it is a real operator boundary
```

## Next

```text
0082 notification primitive
0083 lease handoff status
0084 Scheduler handshake integration
```
