# Changelog — 0105 Scheduler priority/admission lock

Added an architecture/rules lock that freezes the priority and admission model:

- PriorityQueue remains the only deterministic execution ordering mechanism.
- PolicyEngine remains minimal admission before queue.
- Dispatcher remains EventType -> Handler only.
- ControlProxy / RouteRuntimeManager does not compute global priorities.
- ControlProxy / RouteRuntimeManager does not decide policy/zone admission.
- EventBus remains observation only.
- Route mmap/eventfd is named as data plane, not EventBus.

No runtime code was changed.
