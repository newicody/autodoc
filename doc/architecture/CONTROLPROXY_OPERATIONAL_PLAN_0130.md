# 0130 operational note — RouteProxy runtime minimal

0130 makes RouteProxy concrete for one local process without creating a daemon.

```text
Scheduler command later
-> RouteProxyRuntimePolicy
-> /dev/shm/autodoc/routes by default
-> writer permit
-> atomic frame write
-> frame read
-> stale marker when context generation advances
-> observation-ready facts
```

The runtime is deliberately small. It does not call Scheduler, PolicyEngine, EventBus, SQL, OpenVINO, Qdrant, GitHub, network clients, or subprocesses.

The next integration step can introduce a thin handler that calls this runtime from the Scheduler/Dispatcher path, while keeping Scheduler.run() unchanged.
