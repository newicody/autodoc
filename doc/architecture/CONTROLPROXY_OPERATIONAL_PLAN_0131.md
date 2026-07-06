# ControlProxy operational plan — 0131

0131 starts the bridge between Scheduler command data and the RouteProxy `/dev/shm` runtime.

```text
Scheduler decides
-> SchedulerRouteHandlerCommand
-> SchedulerRouteHandler minimal executor
-> RouteProxyRuntime writer permit
-> atomic frame write under /dev/shm
-> observation-ready facts
```

ControlProxy/RouteProxy remains a data-plane executor. It does not become Scheduler, PolicyEngine, EventBus, SQL authority, OpenVINO adapter, or Qdrant adapter.

The next phase can add fake specialist workers that read frames written by this handler.
