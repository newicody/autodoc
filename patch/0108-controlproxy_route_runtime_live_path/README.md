# 0108 — ControlProxy route runtime live path

This patch adds a small walking-skeleton runtime scenario after the 0101–0107
architecture simplification locks.

It validates the slice after Dispatcher has selected the thin handler:

```text
ControlProxySchedulerRouteRequestHandler
-> RouteRuntimeManager
-> ControlFS + mmap/eventfd data plane
```

It does not modify Scheduler.run(), Dispatcher, PriorityQueue, PolicyEngine or
EventBus. It does not add a CLI, daemon, watcher, service or new bus.
