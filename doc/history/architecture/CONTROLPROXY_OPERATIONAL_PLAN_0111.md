# ControlProxy operational plan — 0111 update

0111 updates the plan after the simplification locks:

```text
0101 lock architecture simplification
0102 audit existing paths
0103 RouteRuntimeManager
0104 thin handler to RouteRuntimeManager
0105 priority/admission lock
0106 EventBus/data plane boundary lock
0107 graph root alignment
0108 live route runtime walking skeleton
0109 compatibility wrappers registry
0110 specialist/kernel boundary
0111 explicit /dev/shm runtime root for real inter-process data plane
```

## 0111 decision

The next runtime hardening step is the **explicit /dev/shm runtime root**:

```text
specialist command
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> Handler
-> RouteRuntimeManager
-> explicit /dev/shm runtime root
-> mmap/eventfd route data plane
```

The phase keeps these locks:

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

## Not done in 0111

```text
No daemon
No watcher
No OpenRC unit
No Scheduler.run() modification
No Dispatcher expansion
No priority recalculation
No PolicyEngine expansion
No EventBus duplication
No NetworkBridge
No HardwareBridge
```

## Next phase suggestion

0112 should be a concrete integration test that uses `RouteDevShmRuntimePolicy` where `/dev/shm` is available, while keeping file-backed tests as recovery and CI paths.
