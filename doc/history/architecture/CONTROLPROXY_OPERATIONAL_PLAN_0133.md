# 0133 operational note — extend existing handler

0133 follows the 0132 anti-duplication rule.  It extends the existing Scheduler route handler and reuses the existing RouteProxyRuntime.

```text
Scheduler/Dispatcher caller
-> SchedulerRouteHandlerCommand
-> existing scheduler_route_handler_minimal.py
-> existing RouteProxyRuntime
-> route frame write
-> route frame readback
```

ControlProxy/RouteProxy remains data-plane infrastructure.  The handler remains an executor bridge, not an orchestrator.  Scheduler remains orchestration authority.
