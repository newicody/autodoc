# 0112 — Route bridge boundary

- Added `src/runtime/route_bridge_boundary.py`.
- Added runtime tests for bridge declarations and no-effect bridge plans.
- Added rule tests locking the future NetworkBridge/HardwareBridge boundary.
- Added architecture docs and a root-attached `.dot` graph.
- No Scheduler, Dispatcher, PriorityQueue, PolicyEngine, EventBus or route runtime code is modified.
