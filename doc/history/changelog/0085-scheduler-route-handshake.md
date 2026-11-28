# 0085 - Scheduler route handshake

## Added

- `runtime.scheduler_route_handshake`
- `prepare_route_for_scheduler()`
- `publish_scheduler_handshake_to_bus()`
- handshake schema:
  - `missipy.scheduler.route_handshake.v1`
- event topic:
  - `scheduler.route.handshake.ready`
- context topic:
  - `scheduler.route.lease.active`
- tests proving:
  - pump + lease acquire + lease activate
  - idempotent same holder/scope reuse
  - conflict rejection
  - no service/daemon/CLI
  - bus facts are written

## Not added

- No daemon.
- No service.
- No OpenRC.
- No watcher.
- No Scheduler event loop implementation.
- No security policy decision.
- No frame write.
- No notification.
- No live resize.
- No CLI.

## r2

Restores exact rule-test wording: `No CLI`.
