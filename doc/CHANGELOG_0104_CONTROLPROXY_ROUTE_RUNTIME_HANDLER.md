# 0104 — ControlProxy route runtime handler binding

- Added a thin Scheduler-facing runtime binding for ControlProxy route requests.
- Kept `Scheduler.run()`, Dispatcher, PriorityQueue and PolicyEngine untouched.
- Kept EventBus as observation only.
- Kept route mmap/eventfd as data plane, not EventBus.
- Added tests proving the existing `ControlProxySchedulerRouteRequestHandler` injection point can delegate to `RouteRuntimeManager`.
