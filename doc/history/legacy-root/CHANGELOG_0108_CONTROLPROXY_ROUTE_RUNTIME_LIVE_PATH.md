# 0108 — ControlProxy route runtime live path

- Added a runtime walking-skeleton test for the simplified ControlProxy path.
- Validated `Handler -> RouteRuntimeManager -> ControlFS + mmap/eventfd data plane`.
- Kept Scheduler, Dispatcher, PolicyEngine, PriorityQueue and EventBus unchanged.
- Added root-attached runtime graph documentation.
- Added rule tests locking the boundary and preventing bus duplication vocabulary.
