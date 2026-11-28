# ControlProxy operational plan after 0102

0102 audits the existing paths before the next code patch.

## Locked next steps

```text
0102 audit existing paths and duplication risks
0103 introduce RouteRuntimeManager as a narrow runtime facade
0104 slim ControlProxy handler to call RouteRuntimeManager
0105 clarify priority/admission minimalism
0106 enforce EventBus versus data-plane separation
0107 rebuild root and individual graphs after code simplification
```

## 0103 — RouteRuntimeManager constraints

`RouteRuntimeManager` should be a facade over existing runtime primitives, not a scheduler-like coordinator.

Allowed responsibilities:

```text
prepare route runtime state
materialize a generation through the locked materializer
activate a generation through lifecycle primitive
mark draining and closed through lifecycle primitive
cleanup closed generation through lifecycle primitive
resolve explicit placement file/dev_shm
write or expose ControlFS state through existing primitives
```

Forbidden responsibilities:

```text
run a global loop
own or mutate global priority
admit events into the Scheduler queue
replace PolicyEngine
replace Dispatcher
create a new bus
own specialist business logic
own ContextGate or TaskContext authority
turn Qdrant into context authority
```

## 0104 — handler slimming constraints

After 0103, the handler path should be:

```text
Scheduler.run()
-> Dispatcher.dispatch()
-> ControlProxySchedulerRouteRequestHandler.handle()
-> RouteRuntimeManager.prepare_route()
```

Wrappers may remain for compatibility, but their direction must be explicit:

```text
prepare_route_for_scheduler -> wrapper around RouteRuntimeManager
handle_scheduler_route_request -> wrapper around RouteRuntimeManager
```

## 0105 — priority/admission constraints

Priority stays minimal until a separate explicit policy is added.

```text
Event.priority = numeric scheduling input
PolicyEngine = minimal admission gate
PriorityQueue = deterministic ordering
ControlProxy = no global priority calculation
Dispatcher = no priority mutation
Specialist = may request priority through typed intention later
```

## 0106 — bus/data-plane constraints

The route runtime must not introduce a second command or observation bus.

```text
EventBus = observation
Context snapshot = context view
mmap/eventfd = route data plane
RouteMessageJournal = data-plane journal projection
Visualization adapter = reader of existing bus
```

## 0107 — graph constraints

Graphs must show implemented code and marked transitions separately.

```text
implemented = solid edge
planned convergence = dashed edge
forbidden duplicate = explicit note, not hidden
root graph owns the global command path
runtime overlay owns ControlProxy route data plane only
```
