# 0084 - ControlProxy pump/tick

## Added

- `runtime.controlproxy_pump`
- `tick_controlproxy()`
- `route_prepare_decision_from_manifest()`
- pump bus facts:
  - `controlproxy.pump.route_materialized`
  - `controlproxy.pump.route_skipped`
  - `controlproxy.pump.route_error`
  - `controlproxy.pump.active_route`
- tests proving:
  - desired routes materialize to active routes
  - second tick becomes noop/skipped
  - updates are skipped, not live-resized
  - bus facts are written
  - no lease is issued by the pump

## Not added

- No daemon.
- No service.
- No OpenRC.
- No watcher.
- No polling loop.
- No Scheduler call.
- No lease issuing.
- No live resize.
- No CLI.
