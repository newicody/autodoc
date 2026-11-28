# 0081 - ControlProxy active route materializer

## Added

- `runtime.controlproxy_active_routes`
- active route status schema:
  - `missipy.controlproxy.active_route_status.v1`
- materialization bridge:
  - ControlProxy ready decision
  - desired RouteManifest
  - mmap route files
  - ControlFS active manifest/status
- post-materialization RouteProxy dry-run helper
- tests proving active route status and noop reconciliation
- no new CLI

## Not added

- No POSIX `shm_open`.
- No mandatory `/dev/shm`.
- No semaphores/eventfd/futex.
- No daemon.
- No watcher.
- No Scheduler wiring.
- No lease handoff.
- No live resize.
- No inter-process safety.
- No VisPy renderer.

