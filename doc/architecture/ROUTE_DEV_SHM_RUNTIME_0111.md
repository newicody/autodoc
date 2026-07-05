# 0111 — Route /dev/shm runtime boundary

0111 reinforces the real inter-process data plane boundary for route runtime files.
It does not change the micro-kernel. It only prepares an **explicit /dev/shm runtime root** and builds `RouteRuntimeManager` with that root.

## Locked vocabulary

```text
EventBus = observation only
Route mmap/eventfd = data plane, not EventBus
/dev/shm = explicit runtime placement, not a Scheduler shortcut
RouteRuntimeManager = runtime facade, not a scheduler-like coordinator
```

Required phrases kept executable by rule tests:

```text
explicit /dev/shm runtime root
real inter-process data plane
no implicit file fallback
Route mmap/eventfd is data plane, not EventBus
EventBus remains observation only
No ControlProxyBus
No RouteBus
No VisualizationBus
builds RouteRuntimeManager
does not modify Scheduler.run()
PolicyEngine remains minimal admission before queue
PriorityQueue remains deterministic execution order
Dispatcher remains EventType -> Handler only
stdlib only
```

## Why this phase exists

0096 made runtime placement explicit. 0103 introduced `RouteRuntimeManager`. 0111 adds the narrow preparation layer for the real inter-process `/dev/shm` root:

```text
/dev/shm
└── autodoc/
    └── routes-runtime/
        └── <route>@gN/
            ├── ring.bin
            └── status.json
```

This is still the route data plane. It is not a command bus and not an observation bus.

## Safety rules

`route_dev_shm_runtime.py` rejects:

```text
missing root
non-directory root
symlink root
namespace traversal
namespace containing slash or backslash
symlink namespace root
symlink routes-runtime root
non-tmpfs root when require_tmpfs=True
```

There is **no implicit file fallback**. File-backed runtime roots remain valid for tests and recovery, but they are selected through the explicit file placement path, not by silently falling back from `/dev/shm`.

## Kernel boundaries unchanged

```text
Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager
RouteRuntimeManager -> ControlFS + mmap/eventfd data plane
```

0111 does not modify Scheduler, PolicyEngine, PriorityQueue, Dispatcher, Handler, EventBus, or Component contracts.
