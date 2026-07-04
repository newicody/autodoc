# 0079-r2 - ControlProxy sizing, prepare handshake and bus visibility

## Replaces

- Rejected old `0079`.
- Useful protocol part of old `0080`.

## Added

- `ControlProxy = ControlFS + RouteProxy` vocabulary.
- Optional route manifest sizing fields:
  - `transport`
  - `slot_size`
  - `slot_count`
  - `max_frame_bytes`
  - `overflow_policy`
  - `notify`
  - `sizing_source`
  - `observed_frame_bytes`
- `runtime.controlproxy_prepare`
- `missipy.controlproxy.route_prepare_request.v1`
- `missipy.controlproxy.route_prepare_status.v1`
- Zone policy table.
- Bus projection to:
  - `event.bus`
  - `context.bus`
- CLI:
  - `tools/write_baby_fork_controlproxy_sized.py`
  - `tools/prepare_fake_routes_controlproxy.py`
- Architecture audit and index.

## Not added

- No mmap implementation.
- No live mmap resize.
- No semaphore/eventfd/futex implementation.
- No ControlProxy daemon.
- No ControlFS watcher.
- No Scheduler wiring.
- No VisPy renderer.
