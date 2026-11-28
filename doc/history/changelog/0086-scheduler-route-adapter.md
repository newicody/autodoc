# 0086 - Scheduler route adapter

## Added

- `runtime.scheduler_route_adapter`
- `SchedulerRouteRequest`
- `SchedulerRouteReply`
- `handle_scheduler_route_request()`
- `scheduler_route_request_mapping()`
- adapter event topic:
  - `scheduler.route.adapter.ready`
- adapter context topic:
  - `scheduler.route.adapter.reply`
- request schema:
  - `missipy.scheduler.route_adapter_request.v1`
- reply schema:
  - `missipy.scheduler.route_adapter_reply.v1`

## Not added

- No daemon.
- No service.
- No OpenRC.
- No watcher.
- No CLI.
- No Scheduler event loop.
- No PriorityQueue.
- No Dispatcher.
- No PolicyEngine call.
- No security policy decision.
- No manifest generation.
- No frame write.
- No notification.
- No live resize.

## r2

Restores exact rule-test wording: `not the Scheduler loop itself`.
